import abc
import os
import subprocess
import shutil
import imdb
import io
import requests
import json
import re
from PIL import Image

from cache_utilis import cache_path
from const import MEDIA_PLAYER, CACHE_DIR
from errors import MediaNotFoundError, PosterNotFoundError

class Media(abc.ABC):
    def __init__(self):
        pass

    def init_media_from_imdb(self, search: str) -> None:
        cinemagoer = imdb.Cinemagoer()
        search_result = cinemagoer.search_movie(search)
        if not search_result:
            raise MediaNotFoundError(f"Media '{search}' not found in IMDb.")
        self.media = search_result[0]
        cinemagoer.update(self.media)

    def get_image(self):
        poster_url = self.media.get('cover url')
        if not poster_url:
            raise PosterNotFoundError(f"Poster not found for '{self.name}'.")
        response = requests.get(poster_url)
        response.raise_for_status()
        self.image = Image.open(io.BytesIO(response.content))
    
    @property
    def cache_path(self):
        return cache_path(self.path)
    
    @abc.abstractmethod
    def play(self):
        pass

    @abc.abstractmethod
    def save_to_cache(self, cache_file: str):
        pass

    @classmethod
    @abc.abstractmethod
    def load_from_cache(self, cache_file: str):
        pass

class Movie(Media):
    def __init__(
            self,
            path: str,
            from_cache: bool = False,
            **kwargs
        ):
        self.path = path

        if from_cache:
            self._init_from_cache(**kwargs)
            return

        if os.path.isfile(path):
            self.is_file = True
            search = os.path.basename(path).split('.')[0]
        else:
            self.is_file = False
            search = os.path.basename(path)[1:]
        
        self.init_media_from_imdb(search)
        self.name = self.media.get('title')
        self.rating = self.media.get('rating')
        self.year = self.media.get('year')
        self.get_image()
    
    def _init_from_cache(self, name: str, is_file: bool, image: Image, rating: float, year: int):
        self.name = name
        self.is_file = is_file
        self.image = image
        self.rating = rating
        self.year = year

    def play(self):
        if self.is_file:
            subprocess.Popen([MEDIA_PLAYER, self.path])
        else:
            first_file = os.path.join(self.path, os.listdir(self.path)[0])
            subprocess.Popen(f'explorer /select,"{first_file}"')

    def save_to_cache(self):
        os.makedirs(self.cache_path, exist_ok=True)
        image_path = os.path.join(self.cache_path, "image.png")
        json_path = os.path.join(self.cache_path, "metadata.json")
        self.image.save(image_path, format="PNG")
        metadata = {
            'name': self.name,
            'path': self.path,
            'rating': self.rating,
            'year': self.year,
            'is_file': self.is_file,
        }
        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=3)
    
    @classmethod
    def load_from_cache(cls, cache_folder: str):
        image_path = os.path.join(cache_folder, "image.png")
        json_path = os.path.join(cache_folder, "metadata.json")
        with open(json_path, 'r') as f:
            metadata = json.load(f)
        image = Image.open(image_path)
        return cls(
            path=metadata['path'],
            from_cache=True,
            name=metadata['name'],
            is_file=metadata['is_file'],
            image=image,
            rating=metadata['rating'],
            year=metadata['year']
        )

class Show(Media):
    def __init__(
            self,
            path: str,
            from_cache: bool = False,
            **kwargs
        ):
        self.path = path
        self.episode_list = self.get_episode_list()

        if from_cache:
            self._init_from_cache(**kwargs)
            return

        search = os.path.basename(path)
        self.init_media_from_imdb(search)
        self.name = self.media.get('title')
        self.rating = self.media.get('rating')
        self.year = self.media.get('year')
        self.get_image()
    
    def _init_from_cache(self, name: str, image: Image, rating: float, year: int):
        self.name = name
        self.image = image
        self.rating = rating
        self.year = year

    def get_episode_list(self):
        episode_list = []
        for file in os.listdir(self.path):
            if os.path.isfile(os.path.join(self.path, file)):
                episode_list.append(file)
        episode_list.sort(key=self.comapare_episodes)
        return episode_list
    
    @staticmethod
    def comapare_episodes(episode_name: str):
        episode_name = episode_name.split('.')[0]
        episode_list = re.findall(r'\D+|\d+', episode_name)
        episode_digit_list = []
        for episode in episode_list:
            if episode.isdigit():
                episode_digit_list.append(episode)
        episode_digit = ''.join(episode_digit_list)
        if episode_digit == 0:
            return -1
        return int(episode_digit)
    
    def play(self):
        if not os.path.exists(os.path.join(self.path, "watched")):
            os.makedirs(os.path.join(self.path, "watched"))
        
        if self.episode_list:
            current_episode = self.episode_list.pop(0)
            shutil.move(
                os.path.join(self.path, current_episode),
                os.path.join(self.path, "watched", current_episode)
            )
            current_episode = os.path.join(self.path, "watched", current_episode)
            subprocess.Popen([MEDIA_PLAYER, current_episode])

    def save_to_cache(self):
        os.makedirs(self.cache_path, exist_ok=True)
        image_path = os.path.join(self.cache_path, "image.png")
        json_path = os.path.join(self.cache_path, "metadata.json")
        self.image.save(image_path, format="PNG")
        metadata = {
            'name': self.name,
            'path': self.path,
            'rating': self.rating,
            'year': self.year,
        }
        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=2)

    @classmethod
    def load_from_cache(cls, cache_folder: str):
        image_path = os.path.join(cache_folder, "image.png")
        json_path = os.path.join(cache_folder, "metadata.json")
        with open(json_path, 'r') as f:
            metadata = json.load(f)
        image = Image.open(image_path)
        return cls(
            path=metadata['path'],
            from_cache=True,
            name=metadata['name'],
            image=image,
            year=metadata['year'],
            rating=metadata['rating']
        )