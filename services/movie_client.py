import io
from PIL import Image

from services.api_client import ApiClient


class MovieClient(ApiClient):
    BASE_URL = "https://imdb.iamidiotareyoutoo.com"
    
    @classmethod
    def search_media(cls, title: str):
        return cls.get("search", params={"q": title}).json()['description'][0]['#IMDB_ID']
    
    @classmethod
    def get_media(cls, id: str):
        return cls.get(f"search", params={"tt": id}).json()['short']

    @classmethod
    def get_poster(cls, id: str):
        response = cls.get(f"/photo/{id}" ,params={'w': 300, 'h': 440})
        return Image.open(io.BytesIO(response.content))