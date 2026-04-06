import io
from typing import Any

from PIL import Image

from services.api_client import ApiClient
from services.logger import logger


class ImdbdevClient(ApiClient):
    """
    A client for interacting with the imdb.dev API.

    Used mainly as a fallback when the main movie / show clients fail
    """

    BASE_URL = "https://api.imdbapi.dev"

    @classmethod
    def search_media(cls, title: str) -> str:
        logger.debug(f"[Imdbdev] Searching for movie with title: {title}")
        return cls.get("search/titles", params={"query": title}).json()["titles"][0][
            "id"
        ]

    @classmethod
    def get_media(cls, id: str, **kwargs) -> dict[str, Any]:  # noqa: ARG003
        logger.debug(f"[Imdbdev] Getting media with id: {id}")
        return cls.get(f"titles/{id}").json()

    @classmethod
    def get_poster(cls, id: str, **kwargs):  # noqa: ARG003
        logger.debug(f"[Imdbdev] Getting poster for media with id: {id}")
        poster_url = cls.get_media(id)["primaryImage"]["url"]
        response = cls.session.get(poster_url)
        image = Image.open(io.BytesIO(response.content))
        image.thumbnail((300, 440))
        return image.convert("RGB")

    @staticmethod
    def format_for_movie(data: dict) -> dict:
        return {
            "name": data["primaryTitle"],
            "description": data.get("plot", "No description available."),
            "aggregateRating": {"ratingValue": data["rating"]["aggregateRating"]},
            "duration": data["runtimeSeconds"] // 60,
            "datePublished": f"{data['startYear']}-00-00",
        }

    @staticmethod
    def format_for_show(data: dict) -> dict:
        return {
            "name": data["primaryTitle"],
            "summary": data["plot"],
            "rating": {"average": data["rating"]["aggregateRating"]},
            "premiered": f"{data['startYear']}-00-00",
        }

    @classmethod
    def get_search_results(cls, title: str) -> list[dict[str, Any]]:
        try:
            logger.debug(f"[Imdbdev] Searching for movie with title: {title}")
            response = cls.get("search/titles", params={"query": title}).json()[
                "titles"
            ]
            search_results = []
            for item in response:
                search_results.append(
                    {
                        "name": item["primaryTitle"],
                        "year": item.get("startYear", "N/A"),
                        "id": item["id"],
                        "imdb_url": f"https://www.imdb.com/title/{item['id']}/",
                    }
                )
            return search_results
        except Exception as e:
            logger.warning(
                f"Failed to fetch search results using imdb.dev for title '{title}': {e.__class__.__name__} | {e}"
            )
            return []
