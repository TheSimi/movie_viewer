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
    def search_media(cls, title: str) -> tuple[str | None, str | None]:
        tvmaze_id = None
        imdb_id = None
        
        try:
            logger.debug(f"[Tvmaze] Searching for show with title: {title}")
            response = cls.get("/singlesearch/shows", params={"q": title}).json()
            tvmaze_id = response.get('id', None)
            imdb_id = response.get('externals', {}).get('imdb', None)
        except Exception as e:
            logger.warning(f"Failed to search for show with title {title}: {e.__class__.__name__} | {e}")

        if not imdb_id: 
            try:
                logger.debug(f"[Imdbdev] Searching for show with title: {title}")
                imdb_id = ImdbdevClient.search_media(title)
            except Exception as e:
                logger.warning(f"Failed to search for show using imdb.dev with title {title}: {e.__class__.__name__} | {e}")

        if not tvmaze_id and not imdb_id:
            raise ValueError(f"Failed to find show with title {title} on both tvmaze and imdb.dev")
        return tvmaze_id, imdb_id

    @classmethod
    def get_media(cls, id: tuple[str | None, str | None], **kwargs) -> dict[str, Any]:
        tvmaze_id, imdb_id = id
        tvmaze_data = None
        imdb_data = None
        
        if tvmaze_id:
            try:
                logger.debug(f"[Tvmaze] Getting show with id: {tvmaze_id}")
                tvmaze_data = cls.get(f"/shows/{tvmaze_id}", params={"embed": "episodes"}).json()
            except Exception as e:
                logger.warning(f"Failed to fetch data using tvmaze for {tvmaze_id}: {e.__class__.__name__} | {e}")
        
        if imdb_id:
            try:
                logger.debug(f"[Imdbdev] Getting show with id: {imdb_id}")
                imdb_data = ImdbdevClient.get_media(imdb_id, **kwargs)
                imdb_data = ImdbdevClient.format_for_show(imdb_data)
                if tvmaze_data:
                    tvmaze_data['rating'] = imdb_data['rating']
            except Exception as e:
                logger.warning(f"Failed to fetch data using imdb.dev for {imdb_id}: {e.__class__.__name__} | {e}")
        
        return tvmaze_data or imdb_data or {}
        

    @classmethod
    def get_poster(cls, id: tuple[str | None, str | None], **kwargs):  # noqa: ARG003
        tvmaze_id, imdb_id = id
        
        if tvmaze_id:
            try:
                logger.debug(f"[Tvmaze] Getting poster for show with id: {tvmaze_id}")
                posters = [
                    i for i in cls.get(f"/shows/{tvmaze_id}/images").json()
                    if i['type'] == 'poster'
                ]
                main_posters = [i for i in posters if i['main']]
                if main_posters:
                    url = main_posters[0]['resolutions']['original']['url']
                else:
                    url = posters[0]['resolutions']['original']['url']
                response = cls.session.get(url)
                image = Image.open(io.BytesIO(response.content))
                image.thumbnail((300, 440))
                return image.convert("RGB")
            except Exception as e:
                logger.warning(f"Failed to fetch poster with tvmaze for {tvmaze_id}: {e.__class__.__name__} | {e}")
        
        if imdb_id:    
            try:
                logger.debug(f"[Imdbdev] Getting poster for show with id: {imdb_id}")
                return ImdbdevClient.get_poster(imdb_id)
            except Exception as e:
                logger.warning(f"Failed to fetch poster with imdb.dev for {imdb_id}: {e.__class__.__name__} | {e}")
            
        return UNKNOWN_POSTER