import io
from PIL import Image

from services.api_client import ApiClient

class ShowClient(ApiClient):
    BASE_URL = "https://api.tvmaze.com"
    
    @classmethod
    def search_media(cls, title: str) -> str:
        return cls.get("/singlesearch/shows", params={"q": title}).json()['id']

    @classmethod
    def get_media(cls, id: str) -> dict[str, any]:
        return cls.get(f"/shows/{id}").json()
    
    @classmethod
    def get_poster(cls, id: str):
        url: str = [
            i for i in cls.get(f"/shows/{id}/images").json()
            if i['type'] == 'poster'
        ][0]['resolutions']['original']['url']
        print(url)
        response = cls.session.get(url)
        image = Image.open(io.BytesIO(response.content))
        image.thumbnail((300, 440))
        return image.convert("RGB")