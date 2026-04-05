import json
import os
import re
import shutil
import subprocess

from const import MEDIA_PLAYER, SUBTITLE_EXTENTIONS, VIDEO_EXTENTIONS
from media_classes.media import Media
from services.logger import logger
from services.movie_client import MovieClient


class Movie(Media):
    _KEYS = ['is_file', 'name', 'plot', 'rating', 'runtime', 'year', 'image']
    
    def __init__(self, path: str, **kwargs):
        super().__init__(path, client_class=MovieClient, **kwargs)
        if kwargs:
            return
        
        self.is_file = os.path.isfile(self.path)
        
        self.name = self.data.get('name', os.path.splitext(os.path.basename(self.path))[0])
        self.plot = self.data.get('description', '')
        self.rating = self.data.get('aggregateRating', {}).get('ratingValue', 0)
        try:
            self.runtime = int(self.data.get('duration', 0))
        except ValueError:
            self.runtime = self.get_time_from_string(self.data.get('duration', 'PT0H0M'))
        self.year = int(self.data.get('datePublished', '0000-00-00').split('-')[0])
        
        self.save_to_cache()

    @classmethod
    def from_folder(cls, dir_path: str) -> list:
        """
        Loads all the movies from a single given folder, by going through it recursively.
        Every file with a movie extension will be loaded into a Movie object, along with any 
        directory starting with the char '-'
        Movie objects will be loaded from cache if possible.

        :param dir_path: Path to a valid directory
        :type dir_path: str
        :return: A list of Movie objects
        :rtype: list[Movie]
        """
        super().from_folder(dir_path)
        
        media_list = []
        for f in os.listdir(dir_path):
            full_path = os.path.join(dir_path, f)
            cache_path = cls.cache_path(full_path)
            if os.path.isdir(full_path):
                if f.startswith("-"):
                    if os.path.exists(cache_path):
                        new_instance = cls.from_cache(cache_path)
                    else:
                        new_instance = cls(full_path)
                    media_list.append(new_instance)
                else:
                    media_list.extend(cls.from_folder(full_path))
            elif os.path.isfile(full_path) and full_path.endswith(VIDEO_EXTENTIONS):
                if os.path.exists(cache_path):
                    new_instance = cls.from_cache(cache_path)
                else:
                    new_instance = cls(full_path)
                media_list.append(new_instance)

        return media_list

    def save_to_cache(self):
        """
        Saves a media object to cache, creating a cache direcory and saving the image
        and metadata of the movie there
        """
        super().save_to_cache()
        json_path = os.path.join(self.cache_path(self.path), "metadata.json")
        metadata = {
            'name': self.name,
            'path': self.path,
            'rating': self.rating,
            'year': self.year,
            'is_file': self.is_file,
            'metacritic': 0, # TODO - remove metacritic
            'plot': self.plot,
            'runtime': self.runtime
        }
        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=2
        )
    
    def _get_values(self) -> tuple[int, float, str, str, int]:
        """
        Returns a tuple the year, rating, name, path and runtime of the movie, in that order
        
        :return: A tuple with the values of the media
        :rtype: tuple[int, float, str, str, int]
        """
        year, rating, name, path = super()._get_values()
        length: int = getattr(self, 'runtime', 0)
        return year, rating, name, path, length
    
    def play(self, media_player: str = MEDIA_PLAYER, speed: float = 1):
        """
        Plays the movie with the given media player and speed.
        If the movie is a file - plays the file using the given media player and speed.
        If the movie if a folder - tries to either make a playlist of multiple movie files,
        or find a correct subtitles file, and plays them with the given media player and speed.
        
        Works best with VLC, and may not work with other media players.

        :param media_player: The media player executable path to use
        :type media_player: str
        :param speed: The speed to play the media at, defaults to 1
        :type speed: float, optional
        """
        if self.is_file:
            logger.info(f"Playing movie file {self.path} with {media_player} at speed {speed}")
            if self.is_vlc(media_player):
                subprocess.Popen(f'"{media_player}" "{self.path}" --rate={speed} --play-and-exit')
            else:
                logger.warning(f"Playing movie file {self.path} with {media_player} at speed {speed} without speed control, because the media player is not VLC")
                subprocess.Popen(f'"{media_player}" "{self.path}"')
        else:
            files_list = os.listdir(self.path)
            if self.is_vlc(media_player):
                self._play_folder_with_vlc(files_list, media_player, speed)
            else:
                logger.warning(f"Opening movie folder {self.path} because the media player {media_player} is not VLC and not supported for playing folders")
                first_file = os.path.join(self.path, files_list[0])
                subprocess.Popen(f'explorer /select,"{first_file}"')
    
    def _play_folder_with_vlc(self, files_list: list[str], media_player: str, speed: float):
        """
        Plays a folder of videos with VLC, using the given media player and speed.
        If there is only one video file in the folder, it will be played with any subtitles file in the folder.
        If there are multiple video files in the folder, they will all be played in a row as a playlist.
        """
        video_file_list = []
        for file in files_list:
            if file.endswith(VIDEO_EXTENTIONS):
                video_file_list.append(file)
        if len(video_file_list) == 1:
            self._play_file_with_subtitles_vlc(files_list, media_player, speed, video_file_list[0])
        else:
            logger.info(f"Playing movie files {video_file_list} with {media_player} at speed {speed} as a playlist")
            command = f'"{media_player}" '
            for video in video_file_list:
                command += f'"{os.path.join(self.path,  video)}" '
            command += f'--rate={speed} --play-and-exit'
            subprocess.Popen(command)
    
    def _play_file_with_subtitles_vlc(self, files_list, media_player, speed, video_file):
        """
        Plays a single video file with any available subtitle file from the same folder using VLC.
        If there is only one subtitle file, it will be used.
        If there is more than one subtitle file, will try to find a subtitle file with the same name as the video file.
        If there is no subtitle file, it will play the video file without subtitles.
        """
        sub_file = None
        subtitle_file_list = []
        for file in files_list:
            if file.endswith(SUBTITLE_EXTENTIONS):
                subtitle_file_list.append(file)
                    
        if len(subtitle_file_list) == 1:
            sub_file = subtitle_file_list[0]
        else:
            # try and find a subtitle file with the same name as the video
            for sub in subtitle_file_list:
                if os.path.splitext(sub)[0] == os.path.splitext(video_file)[0]:
                    sub_file = sub
                    break
        
        logger.info(f"Playing movie file {video_file} with subtitle file {sub_file} using {media_player} at speed {speed}")
        command = f'"{media_player}" "{os.path.join(self.path, video_file)}" '
        if sub_file is not None:
            command += f'"{os.path.join(self.path, sub_file)}" '
        command += f'--rate={speed} --play-and-exit'
        subprocess.Popen(command)
    
    def open_in_explorer(self):
        """
        Opens the movie in the system's default file explorer.
        If the movie is a file - opens the folder containing the file and selects it.
        If the movie is a folder - opens the folder.
        """
        if not os.path.exists(self.path):
            logger.warning(f"Path {self.path} does not exist, cannot open in explorer")
            return
        if self.is_file:
            logger.info(f"Opening movie file {self.path} in explorer")
            subprocess.Popen(f'explorer /select,"{self.path}"')
        else:
            logger.info(f"Opening movie folder {self.path} in explorer")
            files_list = os.listdir(self.path)
            try:
                file = os.path.join(self.path, files_list[0])
            except IndexError:
                logger.warning(f"Folder {self.path} is empty")
                file = self.path
            subprocess.Popen(f'explorer /select,"{file}"')
    
    def remove_movie(self):
        if self.is_file:
            os.remove(self.path)
        else:
            shutil.rmtree(self.path)
    
    @staticmethod
    def get_time_from_string(time_string: str):
        match = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?', time_string)
    
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
    
        return (hours * 60) + minutes
    