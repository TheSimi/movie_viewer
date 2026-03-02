import re
import os
import json
import shutil
import subprocess

from const import MEDIA_PLAYER
from media_classes.media import Media
from services.logger import logger
from services.show_client import ShowClient

class Show(Media):
    _KEYS = ['name', 'plot', 'rating', 'year', 'episodes', 'seasons', 'image']
    
    def __init__(self, path: str, **kwargs):
        super().__init__(path, client_class=ShowClient, **kwargs)
        if kwargs:
            return
        
        self.name = self.data.get('name', os.path.splitext(os.path.basename(self.path))[0])
        self.plot = re.sub(r'<.*?>', '', self.data.get('summary', ''))
        self.rating = self.data.get('rating', {}).get('average', 0)
        self.year = int(self.data.get('premiered', '0000-00-00').split('-')[0])
        self.episodes = len(self.data.get('_embedded', {}).get('episodes', []))
        self.seasons = max({episode['season'] for episode in self.data.get('_embedded', {}).get('episodes', [])}) if self.data.get('_embedded', {}).get('episodes') else 0
        
        if self.data:
            self.save_to_cache()

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
                        new_instance = cls(full_path)
                    show_list.append(new_instance)
        return show_list

    def save_to_cache(self):
        super().save_to_cache()
        json_path = os.path.join(self.cache_path(self.path), "metadata.json")
        metadata = {
            'name': self.name,
            'path': self.path,
            'rating': self.rating,
            'year': self.year,
            'plot': self.plot,
            'episodes': self.episodes,
            'seasons': self.seasons
        }
        with open(json_path, 'w') as f:
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
    
    @staticmethod
    def _comapare_episodes(episode_name: str):
        episode_name = os.path.splitext(episode_name)[0]
        episode_as_list = re.findall(r'\D+|\d+', episode_name)
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
        length: int = getattr(self, 'episodes', 0)
        return year, rating, name, path, length
    
    def play(self, media_player: str = MEDIA_PLAYER, speed: float = 1):
        if self.episode_list:
            if not os.path.exists(os.path.join(self.path, "watched")):
                os.makedirs(os.path.join(self.path, "watched"))

            current_episode = self.episode_list[0]
            shutil.move(
                os.path.join(self.path, current_episode),
                os.path.join(self.path, "watched", current_episode)
            )
            current_episode = os.path.join(self.path, "watched", current_episode)
            logger.info(f"Playing episode {current_episode} of show {self.name} with {media_player} at speed {speed}")
            if self.is_vlc(media_player):
                subprocess.Popen(f'"{media_player}" "{current_episode}" --rate={speed} --play-and-exit')
            else:
                logger.warning(f"Playing episode {current_episode} of show {self.name} with {media_player} at speed {speed} without speed control, because the media player is not VLC")
                subprocess.Popen(f'"{media_player}" "{current_episode}"')
        else:
            logger.warning(f"No episodes found for show {self.name} in path {self.path}, opening folder instead")
            try:
                file = os.path.join(self.path, os.listdir(self.path)[0])
            except IndexError:
                logger.warning(f"No files in show folder {self.path}")
                file = self.path
            subprocess.Popen(f'explorer /select,"{file}"')
    
    def open_in_explorer(self):
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
    
    def remove_watched_folder(self):
        if os.path.exists(os.path.join(self.path, "watched")):
            shutil.rmtree(os.path.join(self.path, "watched"))