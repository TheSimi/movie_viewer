import abc
import json
import os
import re
import shutil
from typing import Any, ClassVar

from PIL import Image
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from const import CACHE_DIR, MEDIA_PLAYER, UNKNOWN_POSTER
from services.api_client import ApiClient, MediaId
from services.logger import logger


class Media(BaseModel, abc.ABC):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        arbitrary_types_allowed=True,
        extra="ignore",
        validate_assignment=True,
    )

    path: str = Field(...)
    id: MediaId | None = Field(default=None)
    name: str = Field(default="")
    plot: str = Field(default="")
    rating: float = Field(default=0)
    year: int = Field(default=0)
    image: Image.Image = Field(default_factory=lambda: UNKNOWN_POSTER.copy(), exclude=True, repr=False)

    @classmethod
    @abc.abstractmethod
    def _default_client_class(cls) -> type[ApiClient]:
        """Return the ApiClient used by from_path() by default"""
        ...

    @classmethod
    def from_path(cls, path: str, id: MediaId | None = None, client_class: type[ApiClient] | None = None) -> "Media":
        client_class = client_class or cls._default_client_class()
        filename = os.path.splitext(os.path.basename(path))[0]
        try:
            if id is None:
                id = client_class.search_media(filename)
            fetched = client_class.get_media(id, title=filename, path=path)
            if not isinstance(fetched, Media):
                raise TypeError(
                    f"{client_class.__name__}.get_media returned {type(fetched).__name__}, expected a Media model"
                )
            fetched.path = path
            if fetched.id is None:
                fetched.id = id
            fetched.save_to_cache()
            return fetched
        except Exception as e:
            logger.warning(f"Failed to fetch for {filename}: {e.__class__.__name__} | {e}")
            return cls.model_validate({"path": path, "id": id, "image": UNKNOWN_POSTER.copy()})

    @staticmethod
    def _coerce_rating(value: Any) -> float:
        if value is None or value == "" or isinstance(value, bool):
            return 0
        if isinstance(value, dict):
            nested = value.get("ratingValue", value.get("average", 0))
            return Media._coerce_rating(nested)
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0

    _FIELD_ALIASES: ClassVar[dict[str, str]] = {}

    @classmethod
    def _apply_aliases(cls, data: dict[str, Any]) -> dict[str, Any]:
        for canonical, alias in cls._FIELD_ALIASES.items():
            if canonical not in data and alias in data:
                data[canonical] = data.pop(alias)
        return data

    # ---------- shared field validators ----------

    @field_validator("id", mode="before")
    @classmethod
    def _validate_id(cls, v: Any) -> Any:
        if isinstance(v, list):
            return tuple(v)
        return v

    @field_validator("rating", mode="before")
    @classmethod
    def _validate_rating(cls, v: Any) -> float:
        return cls._coerce_rating(v)

    @field_validator("year", mode="before")
    @classmethod
    def _validate_year(cls, v: Any) -> int:
        if v is None or v == "" or isinstance(v, bool):
            return 0
        if isinstance(v, int):
            return v
        if isinstance(v, float):
            return int(v)
        text = str(v).strip()
        if not text:
            return 0
        first = text.split("-")[0].strip()
        try:
            return int(first)
        except ValueError:
            return 0

    @field_validator("plot", mode="before")
    @classmethod
    def _validate_plot(cls, v: Any) -> str:
        if v is None:
            plot = ""
        else:
            plot = str(v)
        # Summaries (TVMaze description) may contain HTML
        return re.sub(r"<.*?>", "", plot)

    @model_validator(mode="after")
    def _fill_name_from_path(self) -> "Media":
        if not self.name and self.path:
            self.name = os.path.splitext(os.path.basename(self.path))[0]
        return self

    @staticmethod
    def cache_path(path: str) -> str:
        basename = os.path.basename(path)
        # sum the values of the characters in the path
        char_sum = 0
        for i in path:
            char_sum += ord(i)
        basename = basename + "_" + str(char_sum)
        return os.path.join(CACHE_DIR, basename)

    @staticmethod
    def is_vlc(media_player: str) -> bool:
        return os.path.basename(media_player).lower() in ["vlc", "vlc.exe"]

    @classmethod
    def from_cache(cls, path: str) -> "Media":
        """
        Loads a media object from cache

        :param path: Path to a valid cache directory
        :type path: str
        :return: A new Media object
        :rtype: Media
        """
        image_path = os.path.join(path, "image.png")
        json_path = os.path.join(path, "metadata.json")
        with open(json_path) as f:
            data = json.load(f)
        image = Image.open(image_path).convert("RGB")
        return cls.model_validate({**data, "image": image})

    @abc.abstractmethod
    def save_to_cache(self) -> None:
        """
        Saves a media object to cache, needs to be implemented on every subclass
        The default implementation creates the cache directory and saves self.image there
        """
        cache_path = self.cache_path(self.path)
        os.makedirs(cache_path, exist_ok=True)
        image_path = os.path.join(cache_path, "image.png")
        img = self.image
        if hasattr(img, "info") and isinstance(img.info, dict):
            img.info.pop("icc_profile", None)
        img.save(image_path)

    @abc.abstractmethod
    def _get_values(self) -> tuple:
        """
        Returns a tuple with the values of the media. Needs to be implemented on every subclass
        Default implementation returns year, rating, name and path fo the media

        :return: A tuple with the values of the media
        :rtype: tuple[int, float, str, str]
        """
        year: int = getattr(self, "year", 0)
        rating: float = getattr(self, "rating", 0.1)
        name: str = getattr(self, "name", "placeholder")
        path: str = getattr(self, "path", "placeholder")
        return year, rating, name, path

    @classmethod
    @abc.abstractmethod
    def from_folder(cls, dir_path: str) -> list:
        """
        Loads a type of media from a given directory, needs to be implemented on every subclass
        Default implementation only checks that dir_path is a directory, and returns an empty list

        :param dir_path: Path to a valid directory
        :type dir_path: str
        :return: A list of Media objects
        :rtype: list[Media]
        """
        if not os.path.isdir(dir_path):
            raise ValueError(f"{dir_path} is not a directory")
        return []

    @abc.abstractmethod
    def play(self, media_player: str = MEDIA_PLAYER, speed: float = 1) -> None:
        """
        Plays the media with the given media player and speed.
        Needs to be implemented on every subclass, default implementation does nothing.

        :param media_player: The media player executable path to use
        :type media_player: str
        :param speed: The speed to play the media at, defaults to 1
        :type speed: float, optional
        """
        pass

    @abc.abstractmethod
    def open_in_explorer(self) -> None:
        """
        Opens the media in the system's default file explorer.
        Needs to be implemented on every subclass, default implementation does nothing.
        """
        pass

    @abc.abstractmethod
    def remove_media(self) -> None:
        """
        Remove all the media files
        """
        pass

    def delete_cache(self) -> None:
        cache_path = self.cache_path(self.path)
        if os.path.exists(cache_path):
            shutil.rmtree(cache_path)
