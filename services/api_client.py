import abc
from typing import Any

from PIL import Image
from pydantic import BaseModel, ConfigDict, field_validator
from requests import Response, Session
from requests.exceptions import HTTPError

from const import RETRY_AMOUNT
from services.logger import logger

# either just an imdb id (e.g tt0133093) or a tvmaze id (e.g 82),
# or a tuple of (tvmaze_id, imdb_id) - e.g (82, tt0944947)
MediaId = str | int | tuple[str | int | None, str | None] | None


class SearchResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = ""
    year: str = "N/A"
    id: MediaId = None
    imdb_url: str = ""

    @field_validator("year", mode="before")
    @classmethod
    def _coerce_year(cls, v: Any) -> str:
        if not v:
            return "N/A"
        return str(v)

    @field_validator("id", mode="before")
    @classmethod
    def _coerce_id(cls, v: Any) -> MediaId:
        if isinstance(v, list):
            return tuple(v)
        return v


class ApiClient(abc.ABC):
    BASE_URL: str
    session = Session()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Ensure the subclass isn't just another abstract class
        if abc.abstractmethod not in cls.__dict__.values():
            if not hasattr(cls, "BASE_URL"):
                raise TypeError(f"Class {cls.__name__} must define 'BASE_URL'")

    @classmethod
    def request(cls, method: str, url: str, *args: Any, **kwargs: Any) -> Response:
        for attempt in range(RETRY_AMOUNT):
            try:
                full_url = f"{cls.BASE_URL}/{url}"
                logger.debug(f"Request Attemp #{attempt + 1}: {method} {full_url}")
                response = cls.session.request(method, full_url, *args, **kwargs)
                response.raise_for_status()
                return response
            except HTTPError as e:
                logger.error(f"Failed to make request to {url}: {e.response.status_code} | {e.response.text}")
        raise Exception(f"Failed to make request to {url} after {RETRY_AMOUNT} attempts")

    @classmethod
    def get(cls, url: str, *args: Any, **kwargs: Any) -> Response:
        return cls.request("GET", url, *args, **kwargs)

    @classmethod
    @abc.abstractmethod
    def search_media(cls, title: str) -> MediaId:
        """
        Search for a media and return its id

        :param title: The title of the media
        :type title: str
        :return: The media id
        :rtype: MediaId
        """
        ...

    @classmethod
    @abc.abstractmethod
    def get_media(cls, id: MediaId, **kwargs: Any) -> dict[str, Any] | BaseModel:
        """
        Get a media by its id.

        Low-level clients (e.g WikiClient) return raw dicts,
        High-level ones (e.g MovieClient) return validated Movie/Show models.
        """
        ...

    @classmethod
    @abc.abstractmethod
    def get_poster(cls, id: MediaId, **kwargs: Any) -> Image.Image:
        """
        Get a media poster by it's id

        :param id: The id of the media
        :type id: MediaId
        :return: The media poster in a 300x440 resolution
        :rtype: Image.Image
        """
        ...

    @classmethod
    @abc.abstractmethod
    def get_search_results(cls, title: str) -> list[SearchResult]:
        """
        Get search results for a media title

        :param title: The title of the media
        :type title: str
        :return: A list of validated search results
        :rtype: list[SearchResult]
        """
        ...
