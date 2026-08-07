import io
from typing import Any

from PIL import Image

from services.api_client import ApiClient, MediaId
from services.logger import logger


class FmdbClient(ApiClient):
    BASE_URL = "https://imdb.iamidiotareyoutoo.com"

    @classmethod
    def search_media(cls, title: str):
        logger.debug(f"[FM-DB] Searching for movie with title: {title}")
        return cls.get("search", params={"q": title}).json()["description"][0]["#IMDB_ID"]

    @classmethod
    def get_media(cls, id: MediaId, title: str | None = None, **kwargs) -> dict[str, Any]:  # noqa: ARG003
        logger.debug(f"[FM-DB] Getting movie with id: {id}")
        data = cls.get("search", params={"tt": id}).json()["short"]
        if title:
            try:
                data["name"] = cls.get_media_name(title)
            except Exception as e:
                logger.warning(f"Failed to fetch media name for title {title}: {e.__class__.__name__} | {e}")
        return data

    @classmethod
    def get_media_name(cls, title: str) -> str:
        """
        Fetch the name of a media item by its title.

        This is used because when dealing with a foriegn movie, the fm-db api returns
        the title in the original language, so we need to make another request to get the english title.
        """
        logger.debug(f"[FM-DB] Getting media name for title: {title}")
        return cls.get("search", params={"q": title}).json()["description"][0]["#TITLE"]

    @classmethod
    def get_media_by_title(cls, title: str) -> dict[str, Any]:
        """
        Get limited media data by title,
        could be used as a fallback when the id is not found.
        Only returns the name and year fields.
        """
        logger.debug(f"[FM-DB] Trying to get media by title: {title}")
        data = cls.get("search", params={"q": title}).json()["description"][0]
        return {
            "name": data.get("#TITLE", title),
            "datePublished": f"{data.get('#YEAR', '0000')}-00-00",
        }

    @classmethod
    def get_poster(cls, id: MediaId, **kwargs) -> Image.Image:  # noqa: ARG003
        logger.debug(f"[FM-DB] Getting poster for movie with id: {id}")
        response = cls.get(f"/photo/{id}", params={"w": 300, "h": 440})
        return Image.open(io.BytesIO(response.content))

    @classmethod
    def get_poster_by_title(cls, title: str):
        """
        Get a poster for a movie by its title,
        could be used as a fallback when the id is not found.
        Fetches the image from imdb instead of the free movie database
        """
        logger.debug(f"[FM-DB] Trying to get poster by title: {title}")
        data = cls.get("search", params={"q": title}).json()["description"][0]
        poster_url = data.get("#IMG_POSTER", "")
        response = cls.session.get(poster_url)
        image = Image.open(io.BytesIO(response.content))
        image.thumbnail((300, 440))
        return image.convert("RGB")

    @classmethod
    def get_search_results(cls, title: str) -> list[dict[str, Any]]:
        logger.debug(f"[FM-DB] Getting search results for title: {title}")
        response = cls.get("search", params={"q": title}).json()["description"]
        return [
            {
                "name": item.get("#TITLE", ""),
                "year": item.get("#YEAR", ""),
                "id": item.get("#IMDB_ID", ""),
                "imdb_url": item.get("#IMDB_URL", ""),
            }
            for item in response
        ]
