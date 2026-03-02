import abc
from requests import Session, Response
from requests.exceptions import HTTPError
from PIL import Image

from const import RETRY_AMOUNT
from services.logger import logger


class ApiClient:
    __metaclass__ = abc.ABCMeta
    
    BASE_URL: str
    session = Session()
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        
        # Ensure the subclass isn't just another abstract class
        if not abc.abstractmethod in cls.__dict__.values():
            if not hasattr(cls, "BASE_URL"):
                raise TypeError(f"Class {cls.__name__} must define 'BASE_URL'")
    
    @classmethod
    def request(cls, method, url, *args, **kwargs) -> Response:
        for attempt in range(RETRY_AMOUNT):
            try:
                full_url = f"{cls.BASE_URL}/{url}"
                logger.debug(f"Request Attemp #{attempt + 1}: {method} {full_url}")
                response = cls.session.request(method, full_url, *args, **kwargs)
                response.raise_for_status()
                return response
            except HTTPError as e:
                logger.error(f"Failed to make request to {url}: {e.response.status_code} | {e.response.text}")
        raise Exception(f"Failed to make request to {url} after {RETRY_AMOUNT} attempts")

    @classmethod
    def get(cls, url, *args, **kwargs) -> Response:
        return cls.request("GET", url, *args, **kwargs)
    
    @classmethod
    @abc.abstractmethod
    def search_media(cls, title: str) -> str:
        """
        Search for a media and return the imdb id
        
        :param title: The title of the media
        :type title: str
        :return: The imdb media id
        :rtype: str
        """
        ...
    
    @classmethod
    @abc.abstractmethod
    def get_media(cls, id: str) -> dict[str, any]:
        """
        Get a media by it's imdb id
        
        :param id: The id of the media
        :type id: str
        :return: The media data
        :rtype: dict [str, any]
        """
        ...
    
    @classmethod
    @abc.abstractmethod
    def get_poster(cls, id: str) -> Image.Image:
        """
        Get a media poster by it's imdb id
        
        :param id: The id of the media
        :type id: str
        :return: The media poster in a 300x440 resolution
        :rtype: Image.Image
        """
        ...
