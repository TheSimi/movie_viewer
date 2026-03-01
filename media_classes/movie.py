import os
import json

from const import VIDEO_EXTENTIONS
from media_classes.media import Media
from services.movie_client import MovieClient

class Movie(Media):
    _KEYS = ['is_file', 'name', 'plot', 'rating', 'runtime', 'year', 'image']
    
    def __init__(self, path: str, **kwargs):
        super().__init__(path, client_class=MovieClient, **kwargs)
        if kwargs:
            return
        
        self.is_file = os.path.isfile(self.path)
        
        self.name = self.data['name']
        self.plot = self.data['description']
        self.rating = self.data['aggregateRating']['ratingValue']
        self.runtime = self.data['duration']
        self.year = int(self.data['datePublished'].split('-')[0])

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
            if os.path.isdir(full_path):
                if f.startswith("-"):
                    if cls.cache_path(full_path):
                        new_instance = cls.from_cache(cls.cache_path(full_path))
                    else:
                        new_instance = cls(full_path)
                    media_list.append(new_instance)
                else:
                    media_list.extend(cls.from_folder(full_path))
            elif os.path.isfile(full_path) and full_path.endswith(VIDEO_EXTENTIONS):
                if cls.cache_path(dir_path):
                    new_instance = cls.from_cache(cls.cache_path(full_path))
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