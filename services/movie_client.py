import io
from typing import Optional
from PIL import Image

from const import UNKNOWN_POSTER
from services.api_client import ApiClient
from services.logger import logger


class MovieClient(ApiClient):
    BASE_URL = "https://imdb.iamidiotareyoutoo.com"
    
    @classmethod
    def search_media(cls, title: str):
        logger.debug(f"Searching for movie with title: {title}")
        return cls.get("search", params={"q": title}).json()['description'][0]['#IMDB_ID']
    
    @classmethod
    def get_media(cls, id: str, title: Optional[str] = None, **kwargs):
        try:
            logger.debug(f"Getting movie with id: {id}")
            return cls.get(f"search", params={"tt": id}).json()['short']
        except Exception as e:
            logger.warning(f"Failed to fetch data for {id}: {e.__class__.__name__} | {e}")
            if title:
                return cls.get_media_by_title(title)
            return {}
    
    @classmethod
    def get_media_by_title(cls, title: str):
        """
        Get limited media data by title,
        used as a fallback when the id is not found.
        Only returns the name and year fields.
        """
        logger.debug(f"Trying to get media by title: {title}")
        try:
            data = cls.get("search", params={"q": title}).json()['description'][0]
            return {
                'name': data.get('#TITLE', title),
                'datePublished': f"{data.get('#YEAR', '0000')}-00-00",
            }
        except Exception as e:
            logger.warning(f"Failed to get media for title {title}: {e.__class__.__name__} | {e}")
            return {}

    @classmethod
    def get_poster(cls, id: str, title: Optional[str] = None, **kwargs):
        try:
            logger.debug(f"Getting poster for movie with id: {id}")
            response = cls.get(f"/photo/{id}" ,params={'w': 300, 'h': 440})
            return Image.open(io.BytesIO(response.content))
        except Exception as e:
            logger.warning(f"Failed to fetch poster for {id}: {e.__class__.__name__} | {e}")
            if title:
                return cls.get_poster_by_title(title)
            return UNKNOWN_POSTER
    
    @classmethod
    def get_poster_by_title(cls, title: str):
        """
        Get a poster for a movie by its title, used as a fallback when the id is not found.
        Fetches the image from imdb instead of the free movie database
        """
        logger.debug(f"Trying to get poster by title: {title}")
        try:
            data = cls.get("search", params={"q": title}).json()['description'][0]
            poster_url = data.get('#IMG_POSTER', '')
            response = cls.session.get(poster_url)
            image = Image.open(io.BytesIO(response.content))
            image.thumbnail((300, 440))
            return image.convert("RGB")
        except Exception as e:
                logger.warning(f"Failed to fetch poster for title {title}: {e.__class__.__name__} | {e}")
                return UNKNOWN_POSTER