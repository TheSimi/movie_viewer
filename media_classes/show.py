import re
import os
import json

from media_classes.media import Media
from services.show_client import ShowClient

class Show(Media):
    _KEYS = ['name', 'plot', 'rating', 'year', 'episodes', 'seasons', 'image']
    
    def __init__(self, path: str, **kwargs):
        super().__init__(path, client_class=ShowClient, **kwargs)
        if kwargs:
            return
        
        self.name = self.data['name']
        self.plot = re.sub(r'<.*?>', '', self.data['summary'])
        self.rating = self.data['rating']['average']
        self.year = self.data['premiered'].split('-')[0]
        self.episodes = len(self.data['_embedded']['episodes'])
        self.seasons = max({episode['season'] for episode in self.data['_embedded']['episodes']})

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
                    if cls.cache_path(full_path):
                        new_instance = cls.from_cache(cls.cache_path(full_path))
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
    
    def _get_values(self) -> tuple[int, float, str, str, int]:
        """
        Returns a tuple the year, rating, name, path and episode count of the show, in that order
        
        :return: A tuple with the values of the media
        :rtype: tuple[int, float, str, str, int]
        """
        year, rating, name, path = super()._get_values()
        length: int = getattr(self, 'episodes', 0)
        return year, rating, name, path, length