import io
from typing import Any
from PIL import Image

from const import UNKNOWN_POSTER
from services.api_client import ApiClient
from services.imdbdev_client import ImdbdevClient
from services.logger import logger

class ShowClient(ApiClient):
    BASE_URL = "https://api.tvmaze.com"
    
    @classmethod
    def search_media(cls, title: str) -> str:
        try:
            logger.debug(f"Searching for show with title: {title}")
            return cls.get("/singlesearch/shows", params={"q": title}).json()['id']
        except Exception as e:
            logger.warning(f"Failed to search for show using tvmaze with title {title}: {e.__class__.__name__} | {e}")
            return ImdbdevClient.search_media(title)

    @classmethod
    def get_media(cls, id: str, **kwargs) -> dict[str, Any]:
        try:
            logger.debug(f"Getting show with id: {id}")
            return cls.get(f"/shows/{id}", params={"embed": "episodes"}).json()
        except Exception as e:
            logger.warning(f"Failed to fetch data using tvmaze for {id}: {e.__class__.__name__} | {e}")
            try:
                data = ImdbdevClient.get_media(id, **kwargs)
                return ImdbdevClient.format_for_show(data)
            except Exception as e:
                logger.warning(f"Failed to fetch data using imdb.dev for {id}: {e.__class__.__name__} | {e}")
                return {}

    @classmethod
    def get_poster(cls, id: str, **kwargs):
        try:
            logger.debug(f"Getting poster for show with id: {id}")
            url: str = [
                i for i in cls.get(f"/shows/{id}/images").json()
                if i['type'] == 'poster'
            ][0]['resolutions']['original']['url']
            response = cls.session.get(url)
            image = Image.open(io.BytesIO(response.content))
            image.thumbnail((300, 440))
            return image.convert("RGB")
        except Exception as e:
            try:
                logger.warning(f"Failed to fetch poster with tvmaze for {id}: {e.__class__.__name__} | {e}")
                return ImdbdevClient.get_poster(id)
            except Exception as e:
                logger.warning(f"Failed to fetch poster with imdb.dev for {id}: {e.__class__.__name__} | {e}")
                return UNKNOWN_POSTER