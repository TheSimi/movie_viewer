import abc
import os
import subprocess
import shutil
import imdb
import io
import requests
import json
from PIL import Image
from uuid import uuid4

from const import MEDIA_PLAYER, CACHE_DIR
from errors import MediaNotFoundError, PosterNotFoundError

class Media(abc.ABC):
    def __init__(self):
        pass

    def get_media_from_imdb(self, search: str):
        self.cinemagoer = imdb.Cinemagoer()
        search_result = self.cinemagoer.search_movie(search)
        if not search_result:
            raise MediaNotFoundError(f"Media '{search}' not found in IMDb.")
        self.media = search_result[0]
        self.cinemagoer.update(self.media)
        return self.media.get('title')

    def get_image(self):
        poster_url = self.media.get('cover url')
        if not poster_url:
            raise PosterNotFoundError(f"Poster not found for '{self.name}'.")
        response = requests.get(poster_url)
        response.raise_for_status()
        self.image = Image.open(io.BytesIO(response.content))
    
    @property
    def cache_path(self):
        return os.path.join(CACHE_DIR, "+".join(self.path.split(os.sep)))
    
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
            self, path: str,
            name: str = None,
            is_file: bool = None,
            image: Image = None,
            from_cache: bool = False
        ):
        self.path = path

        if from_cache:
            self.name = name
            self.is_file = is_file
            self.image = image
            return

        if os.path.isfile(path):
            self.is_file = True
            search = os.path.basename(path).split('.')[0]
        else:
            self.is_file = False
            search = os.path.basename(path)[1:]
        
        self.name = self.get_media_from_imdb(search)
        print(f"Movie name: {self.name}")
        self.get_image()
    
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
            name=metadata['name'],
            is_file=metadata['is_file'],
            image=image,
            from_cache=True
        )

class Show(Media):
    def __init__(
            self, path: str,
            name: str = None,
            image: Image = None,
            from_cache: bool = False
        ):
        self.path = path
        self.episode_list = self.get_episode_list()

        if from_cache:
            self.name = name
            self.image = image
            return

        search = os.path.basename(path)
        self.name = self.get_media_from_imdb(search)
        print(f"Show name: {self.name}")
        self.get_image()
    
    def get_episode_list(self):
        episode_list = []
        for file in os.listdir(self.path):
            if os.path.isfile(os.path.join(self.path, file)):
                episode_list.append(file)
        return episode_list
    
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
            name=metadata['name'],
            image=image,
            from_cache=True
        )