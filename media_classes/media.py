import abc
import json
import os
import shutil
from typing import Type
from PIL import Image

from const import CACHE_DIR, MEDIA_PLAYER, UNKNOWN_POSTER
from services.api_client import ApiClient
from services.logger import logger

class Media(abc.ABC):
    _KEYS: list[str]
    name: str
    year: int
    rating: float
    plot: str
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        
        # Ensure the subclass isn't just another abstract class
        if abc.abstractmethod not in cls.__dict__.values():
            if not hasattr(cls, "_KEYS"):
                raise TypeError(f"Class {cls.__name__} must define '_KEYS'")
    
    @abc.abstractmethod
    def __init__(
        self,
        path: str,
        client_class: Type[ApiClient] = ApiClient,
        **kwargs
    ):
        # fetch the data
        self.path = path
        if kwargs:
            self.init_kwargs(**kwargs)
            return
        filename = os.path.splitext(os.path.basename(self.path))[0]
        try:
            self.id = client_class.search_media(filename)
            self.data = client_class.get_media(self.id, title=filename)
            self.image = client_class.get_poster(self.id, title=filename)
        except Exception as e:
            logger.warning(f"Failed to fetch for {filename}: {e.__class__.__name__} | {e}")
            self.data = {}
            self.image = UNKNOWN_POSTER
    
    def init_kwargs(self, **kwargs):
        # ensure all required arguments are present
        for key in self._KEYS:
            if key not in kwargs.keys():
                raise ValueError(f"Missing required argument '{key}'")
        
        # set the arguments to the given kwargs
        for key, value in kwargs.items():
            if key in self._KEYS:
                setattr(self, key, value)
            elif not key == 'metacritic': # TODO - remove metacritic
                raise ValueError(f"Invalid argument '{key}'")
    
    @staticmethod
    def cache_path(path: str):
        basename = os.path.basename(path)
        # sum the values of the characters in the path
        char_sum = 0
        for i in path:
            char_sum += ord(i)
        basename = basename + '_' + str(char_sum)
        return os.path.join(CACHE_DIR, basename)
    
    @staticmethod
    def is_vlc(media_player: str):
        return os.path.basename(media_player).lower() in ['vlc', 'vlc.exe']

    @classmethod
    def from_cache(cls, path: str):
        """
        Loads a media object from cache

        :param path: Path to a valid cache directory
        :type path: str
        :return: A new Media object
        :rtype: Media
        """
        image_path = os.path.join(path, "image.png")
        json_path = os.path.join(path, "metadata.json")
        with open(json_path, 'r') as f:
            data = json.load(f)
        image = Image.open(image_path)
        return cls(image=image, **data)
    
    @abc.abstractmethod
    def save_to_cache(self):
        """
        Saves a media object to cache, needs to be implemented on every subclass
        The default implementation creates the cache directory and saves self.image there
        """
        cache_path = self.cache_path(self.path)
        os.makedirs(cache_path, exist_ok=True)
        image_path = os.path.join(cache_path, "image.png")
        self.image.save(image_path)
    
    @abc.abstractmethod
    def _get_values(self) -> tuple:
        """
        Returns a tuple with the values of the media. Needs to be implemented on every subclass
        Default implementation returns year, rating, name and path fo the media
        
        :return: A tuple with the values of the media
        :rtype: tuple[int, float, str, str]
        """
        year: int = getattr(self, 'year', 0)
        rating: float = getattr(self, 'rating', 0.1)
        name: str = getattr(self, 'name', "placeholder")
        path: str = getattr(self, 'path', "placeholder")
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
    def play(self, media_player: str = MEDIA_PLAYER, speed: float = 1):
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
    def open_in_explorer(self):
        """
        Opens the media in the system's default file explorer.
        Needs to be implemented on every subclass, default implementation does nothing.
        """
        pass
    
    def delete_cache(self):
        cache_path = self.cache_path(self.path)
        if os.path.exists(cache_path):
            shutil.rmtree(cache_path)