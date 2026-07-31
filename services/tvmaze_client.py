import io
from typing import Any

from PIL import Image

from services.api_client import ApiClient
from services.logger import logger


class TvmazeClient(ApiClient):
    BASE_URL = "https://api.tvmaze.com"

    @classmethod
    def search_media(cls, title: str) -> tuple[str | None, str | None]:
        logger.debug(f"[Tvmaze] Searching for show with title: {title}")
        response = cls.get("/singlesearch/shows", params={"q": title}).json()
        tvmaze_id = response.get("id", None)
        imdb_id = response.get("externals", {}).get("imdb", None)
        return tvmaze_id, imdb_id

    @classmethod
    def get_media(cls, id: str, **kwargs) -> dict[str, Any]:  # noqa: ARG003
        logger.debug(f"[Tvmaze] Getting show with id: {id}")
        return cls.get(f"/shows/{id}", params={"embed": "episodes"}).json()

    @classmethod
    def get_poster(cls, id: str, **kwargs) -> Image.Image:  # noqa: ARG003
        logger.debug(f"[Tvmaze] Getting poster for show with id: {id}")
        posters = [i for i in cls.get(f"/shows/{id}/images").json() if i["type"] == "poster"]
        main_posters = [i for i in posters if i["main"]]
        if main_posters:
            url = main_posters[0]["resolutions"]["original"]["url"]
        else:
            url = posters[0]["resolutions"]["original"]["url"]
        response = cls.session.get(url)
        image = Image.open(io.BytesIO(response.content))
        image.thumbnail((300, 440))
        return image.convert("RGB")

    @classmethod
    def get_search_results(cls, title: str) -> list[dict[str, Any]]:
        logger.debug(f"[Tvmaze] Getting search results for title: {title}")
        response = cls.get("/search/shows", params={"q": title}).json()
        search_results = []
        for item in response:
            info = item["show"]
            year = info["premiered"].split("-")[0] if info["premiered"] else "N/A"
            search_results.append(
                {
                    "name": info["name"],
                    "year": year,
                    "id": (info["id"], info["externals"]["imdb"]),
                    "imdb_url": f"https://www.imdb.com/title/{info['externals']['imdb']}",
                }
            )
        return search_results
