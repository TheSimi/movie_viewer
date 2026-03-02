import io
from PIL import Image

from const import UNKNOWN_POSTER
from services.api_client import ApiClient
from services.logger import logger

class ShowClient(ApiClient):
    BASE_URL = "https://api.tvmaze.com"
    
    @classmethod
    def search_media(cls, title: str) -> str:
        logger.debug(f"Searching for show with title: {title}")
        return cls.get("/singlesearch/shows", params={"q": title}).json()['id']

    @classmethod
    def get_media(cls, id: str, **kwargs) -> dict[str, any]:
        try:
            logger.debug(f"Getting show with id: {id}")
            return cls.get(f"/shows/{id}", params={"embed": "episodes"}).json()
        except Exception as e:
            logger.warning(f"Failed to fetch data for {id}: {e.__class__.__name__} | {e}")
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
            logger.warning(f"Failed to fetch poster for {id}: {e.__class__.__name__} | {e}")
            return UNKNOWN_POSTER