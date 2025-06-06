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
from const import MEDIA_PLAYER, VIDEO_EXTENTIONS, SUBTITLE_EXTENTIONS
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
        poster_url = self.media.get('full-size cover url')
        if not poster_url:
            raise PosterNotFoundError(f"Poster not found for '{self.name}'.")
        response = requests.get(poster_url)
        response.raise_for_status()
        self.image = Image.open(io.BytesIO(response.content))
        self.image.thumbnail((300, 440))
    
    @property
    def cache_path(self):
        return cache_path(self.path)
    
    @abc.abstractmethod
    def play(self, media_player: str = MEDIA_PLAYER, speed: float = 1):
        pass

    @abc.abstractmethod
    def save_to_cache(self, cache_file: str):
        pass

    @classmethod
    @abc.abstractmethod
    def load_from_cache(self, cache_file: str):
        pass

    def _get_values(self):
        year = self.year if not self.year is None else 1800
        rating = self.rating if not self.rating is None else 0.1
        name = self.name if not self.name is None else "placeholder"
        path = self.path if not self.path is None else "placeholder"
        return year, rating, name, path

class Movie(Media):
    def __init__(
            self,
            path: str,
            from_cache: bool = False,
            **kwargs
        ):
        super().__init__()

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

    def play(self, media_player: str = MEDIA_PLAYER, speed: float = 1):
        if self.is_file:
            print(f'"{media_player}" "{self.path}"')
            if os.path.basename(media_player) == "vlc.exe":
                subprocess.Popen(f'"{media_player}" "{self.path}" --rate={speed} --play-and-exit')
            else:
                subprocess.Popen(f'"{media_player}" "{self.path}"')
        else:
            files_list = os.listdir(self.path)
            if os.path.basename(media_player) == "vlc.exe":
                # get the video list
                video_list = []
                for file in files_list:
                    if file.endswith(VIDEO_EXTENTIONS):
                        video_list.append(file)
                
                if len(video_list) == 1:
                    video_file = video_list[0]
                    sub_file = None

                    # get the subtitle list
                    subtitle_list = []
                    for file in files_list:
                        if file.endswith(SUBTITLE_EXTENTIONS):
                            subtitle_list.append(file)
                    
                    # if there is only 1 subtitle file
                    if len(subtitle_list) == 1:
                        # play the 1 video with the 1 subtitle file
                        sub_file = subtitle_list[0]
                    else:
                        # try and find a subtitle file with the same name as the video
                        for sub in subtitle_list:
                            if os.path.splitext(sub) == os.path.splitext(video_file):
                                sub_file = sub
                                break
                    
                    command = f'"{media_player}" {os.path.join(self.path,  video_file)} '
                    if not sub_file is None:
                        command += f'{os.path.join(self.path, sub_file)} '
                    command += f'--rate={speed} --play-and-exit'
                    subprocess.Popen(command)
                else:
                    # play them all in a row as a playlist
                    command = f'"{media_player}" '
                    for video in video_list:
                        command += os.path.join(self.path,  video)
                        command += " "
                    command += f'--rate={speed} --play-and-exit'
                    subprocess.Popen(command)
            else:
                first_file = os.path.join(self.path, files_list[0])
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
        super().__init__()

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
            if os.path.isfile(os.path.join(self.path, file)) and file.endswith(VIDEO_EXTENTIONS):
                episode_list.append(file)
        episode_list.sort(key=self.comapare_episodes)
        return episode_list
    
    @staticmethod
    def comapare_episodes(episode_name: str):
        episode_name = episode_name.split('.')[0]
        episode_as_list = re.findall(r'\D+|\d+', episode_name)
        episode_digit_list = []
        for episode in episode_as_list:
            if episode.isdigit():
                episode_digit_list.append(episode)
        return episode_digit_list
    
    def play(self, media_player: str = MEDIA_PLAYER, speed: float = 1):
        if not os.path.exists(os.path.join(self.path, "watched")):
            os.makedirs(os.path.join(self.path, "watched"))
        
        if self.episode_list:
            current_episode = self.episode_list.pop(0)
            shutil.move(
                os.path.join(self.path, current_episode),
                os.path.join(self.path, "watched", current_episode)
            )
            current_episode = os.path.join(self.path, "watched", current_episode)
            if os.path.basename(media_player) == "vlc.exe":
                subprocess.Popen(f'"{media_player}" "{current_episode}" --rate={speed} --play-and-exit')
            else:
                subprocess.Popen(f'"{media_player}" "{current_episode}"')

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