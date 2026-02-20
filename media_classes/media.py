import abc
import os
from typing import Type

from services.api_client import ApiClient

class Media(abc.ABC):
    @abc.abstractmethod
    def __init__(self, path: str, client_class: Type[ApiClient]):
        # fetch the data
        self.path = path
        filename = os.path.basename(self.path)
        self.id = client_class.search_media(filename)
        self.data = client_class.get_media(self.id)
        self.image = client_class.get_poster(self.id)
        