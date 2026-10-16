import json
import os
import re
import shutil
import subprocess
from typing import Any, ClassVar

from pydantic import Field, field_validator, model_validator

from const import MEDIA_PLAYER
from media_classes.media import Media
from services.logger import logger


class Show(Media):
    episodes: int = Field(0)
    seasons: int = Field(0)

    _FIELD_ALIASES: ClassVar[dict[str, str]] = {
        "plot": "summary",
        "year": "premiered",
    }

    @classmethod
    def _default_client_class(cls) -> Any:
        from services.show_client import ShowClient

        return ShowClient

    @model_validator(mode="before")
    @classmethod
    def _normalize_show_input(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = cls._apply_aliases(dict(data))
        # TVMaze nests episodes under _embedded
        if "episodes" not in data or "seasons" not in data:
            embedded = data.get("_embedded") or {}
            episode_list = embedded.get("episodes", []) if isinstance(embedded, dict) else []
            if "episodes" not in data or data.get("episodes") is None:
                data["episodes"] = len(episode_list)
            if "seasons" not in data or data.get("seasons") is None:
                seasons: set[int] = set()
                for ep in episode_list:
                    if isinstance(ep, dict) and isinstance(ep.get("season"), int):
                        seasons.add(ep["season"])
                data["seasons"] = max(seasons) if seasons else 0
        return data

    @field_validator("episodes", "seasons", mode="before")
    @classmethod
    def _validate_counts(cls, v: Any) -> int:
        if v is None or v == "" or isinstance(v, bool):
            return 0
        try:
            return int(v)
        except (TypeError, ValueError):
            return 0

    @classmethod
    def from_folder(cls, dir_path: str) -> list:
        """
        Loads all shows from a given directory, by going through it and loading every sub-folder
        as a show objects.
        Folders that start with the char '-' fill not be loaded as a Show and will be searched recursivly
        for shows in them.

        :param dir_path: Path to a valid directory
        :type dir_path: str
        :return: A list of Show objects
        :rtype: list[Show]
        """
        super().from_folder(dir_path)

        show_list = []
        for f in os.listdir(dir_path):
            full_path = os.path.join(dir_path, f)
            if os.path.isdir(full_path):
                if f.startswith("-"):
                    return cls.from_folder(full_path)
                else:
                    cache_path = cls.cache_path(full_path)
                    if os.path.exists(cache_path):
                        new_instance = cls.from_cache(cache_path)
                    else:
                        new_instance = cls.from_path(full_path)
                    show_list.append(new_instance)
        return show_list

    def save_to_cache(self) -> None:
        super().save_to_cache()
        json_path = os.path.join(self.cache_path(self.path), "metadata.json")
        metadata = self.model_dump(mode="json")
        metadata.pop("image", None)
        with open(json_path, "w") as f:
            json.dump(metadata, f, indent=2)

    @property
    def episode_list(self) -> list[str]:
        episode_list = []
        for f in os.listdir(self.path):
            full_path = os.path.join(self.path, f)
            if os.path.isfile(full_path):
                episode_list.append(f)
        episode_list.sort(key=self._comapare_episodes)
        return episode_list

    @property
    def watched_episode_list(self) -> list[str]:
        watched_path = os.path.join(self.path, "watched")
        if not os.path.exists(watched_path):
            return []
        episode_list = []
        for f in os.listdir(watched_path):
            full_path = os.path.join(watched_path, f)
            if os.path.isfile(full_path):
                episode_list.append(f)
        episode_list.sort(key=self._comapare_episodes)
        return episode_list

    def play_episode(
        self,
        episode_name: str,
        media_player: str = MEDIA_PLAYER,
        speed: float = 1,
        move_to_watched: bool = True,
    ) -> None:
        episode_path = os.path.join(self.path, episode_name)
        if not os.path.exists(episode_path):
            watched_path = os.path.join(self.path, "watched", episode_name)
            if os.path.exists(watched_path):
                episode_path = watched_path
            else:
                logger.warning(f"Episode {episode_name} not found in {self.path}")
                return

        if move_to_watched:
            if not os.path.exists(os.path.join(self.path, "watched")):
                os.makedirs(os.path.join(self.path, "watched"))
            if os.path.dirname(episode_path) != os.path.join(self.path, "watched"):
                shutil.move(episode_path, os.path.join(self.path, "watched", episode_name))
                episode_path = os.path.join(self.path, "watched", episode_name)

        logger.info(f"Playing episode {episode_name} of show {self.name} with {media_player} at speed {speed}")
        if self.is_vlc(media_player):
            subprocess.Popen(f'"{media_player}" "{episode_path}" --rate={speed} --play-and-exit')
        else:
            logger.warning(
                f"Playing episode {episode_name} of show {self.name} with windows default player without speed control"
            )
            os.startfile(episode_path)

    def toggle_watched(self, episode_name: str) -> None:
        episode_in_main = os.path.join(self.path, episode_name)
        episode_in_watched = os.path.join(self.path, "watched", episode_name)

        if os.path.exists(episode_in_watched):
            shutil.move(episode_in_watched, episode_in_main)
        elif os.path.exists(episode_in_main):
            if not os.path.exists(os.path.join(self.path, "watched")):
                os.makedirs(os.path.join(self.path, "watched"))
            shutil.move(episode_in_main, episode_in_watched)

    @staticmethod
    def _comapare_episodes(episode_name: str) -> list[float]:
        episode_name = os.path.splitext(episode_name)[0]
        episode_as_list = re.findall(r"\D+|\d+", episode_name)
        episode_digit_list = []
        for episode in episode_as_list:
            if episode.isdigit():
                episode_digit_list.append(float(episode))
        return episode_digit_list

    def _get_values(self) -> tuple[int, float, str, str, int]:
        """
        Returns a tuple the year, rating, name, path and episode count of the show, in that order

        :return: A tuple with the values of the media
        :rtype: tuple[int, float, str, str, int]
        """
        year, rating, name, path = super()._get_values()
        length: int = getattr(self, "episodes", 0)
        return year, rating, name, path, length

    def play(self, media_player: str = MEDIA_PLAYER, speed: float = 1) -> None:
        if self.episode_list:
            if not os.path.exists(os.path.join(self.path, "watched")):
                os.makedirs(os.path.join(self.path, "watched"))

            current_episode = self.episode_list[0]
            shutil.move(
                os.path.join(self.path, current_episode),
                os.path.join(self.path, "watched", current_episode),
            )
            current_episode = os.path.join(self.path, "watched", current_episode)
            logger.info(f"Playing episode {current_episode} of show {self.name} with {media_player} at speed {speed}")
            if self.is_vlc(media_player):
                subprocess.Popen(f'"{media_player}" "{current_episode}" --rate={speed} --play-and-exit')
            else:
                logger.warning(
                    f"Playing episode {current_episode} of show {self.name} with windows default player without speed control, because the given media player is not VLC"
                )
                os.startfile(current_episode)
        else:
            logger.warning(f"No episodes found for show {self.name} in path {self.path}, opening folder instead")
            try:
                file = os.path.join(self.path, os.listdir(self.path)[0])
            except IndexError:
                logger.warning(f"No files in show folder {self.path}")
                file = self.path
            subprocess.Popen(f'explorer /select,"{file}"')

    def open_in_explorer(self) -> None:
        if not os.path.exists(self.path):
            logger.warning(f"Path {self.path} does not exist, cannot open in explorer")
            return
        files_list = os.listdir(self.path)
        try:
            file = os.path.join(self.path, files_list[0])
        except IndexError:
            logger.warning(f"Show folder {self.path} is empty")
            file = self.path
        subprocess.Popen(f'explorer /select,"{file}"')

    def remove_watched_folder(self) -> None:
        if os.path.exists(os.path.join(self.path, "watched")):
            shutil.rmtree(os.path.join(self.path, "watched"))

    def remove_media(self) -> None:
        shutil.rmtree(self.path)
