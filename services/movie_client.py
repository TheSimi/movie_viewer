import io
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
    def get_media(cls, id: str):
        try:
            logger.debug(f"Getting movie with id: {id}")
            return cls.get(f"search", params={"tt": id}).json()['short']
        except Exception as e:
            logger.warning(f"Failed to fetch data for {id}: {e.__class__.__name__} | {e}")
            return {}

    @classmethod
    def get_poster(cls, id: str):
        try:
            logger.debug(f"Getting poster for movie with id: {id}")
            response = cls.get(f"/photo/{id}" ,params={'w': 300, 'h': 440})
            return Image.open(io.BytesIO(response.content))
        except Exception as e:
                logger.warning(f"Failed to fetch poster for {id}: {e.__class__.__name__} | {e}")
                return UNKNOWN_POSTER