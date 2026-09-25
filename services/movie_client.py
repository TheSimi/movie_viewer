from typing import Any

from PIL import Image

from const import UNKNOWN_POSTER
from services.api_client import ApiClient, MediaId
from services.logger import logger
from services.scrape_client import ScrapeClient
from services.wikidata_client import WikidataClient


class MovieClient(ApiClient):
    """
    This client provides logic to search movies using several APIs with fallbacks
    """

    BASE_URL = "https://www.imdb.com"

    @classmethod
    def search_media(cls, title: str):
        try:
            return ScrapeClient.search_media(title)
        except Exception as e:
            logger.warning(
                f"[MovieClient] Failed to search for movie by scraping imdb with title {title}: {e.__class__.__name__} | {e}"
            )
        try:
            return WikidataClient.search_media(title)
        except Exception as e:
            logger.warning(
                f"[MovieClient] Failed to search for movie using wikidata with title {title}: {e.__class__.__name__} | {e}"
            )
            raise

    @classmethod
    def get_media(cls, id: MediaId, title: str | None = None, **kwargs) -> dict[str, Any]:
        """
        Fetch media data by ID.

        Tries to scrape the data directly from imdb.
        If it fails, it will try to fetch data from wikidata (without a rating,
        since only imdb ratings are used).
        When all else fails, returns an empty dict.
        """
        try:
            return ScrapeClient.format_for_movie(ScrapeClient.get_media(id, **kwargs))
        except Exception as e:
            logger.warning(f"[MovieClient] Failed to scrape data from imdb for {id}: {e.__class__.__name__} | {e}")
        try:
            return WikidataClient.get_media(id, title)
        except Exception as e:
            logger.warning(f"[MovieClient] Failed to fetch data from wikidata for {id}: {e.__class__.__name__} | {e}")
        return {}

    @classmethod
    def get_poster(cls, id: MediaId, title: str | None = None, **kwargs) -> Image.Image:  # noqa: ARG003
        """
        Fetch the poster for a movie by its ID.

        Tries to scrape it directly from imdb.
        If it fails, it will try to fetch it from wikidata.
        When all else fails, returns a default unknown poster image.
        """
        try:
            return ScrapeClient.get_poster(id)
        except Exception as e:
            logger.warning(f"[MovieClient] Failed to scrape poster from imdb for {id}: {e.__class__.__name__} | {e}")
        try:
            return WikidataClient.get_poster(id, title)
        except Exception as e:
            logger.warning(f"[MovieClient] Failed to fetch poster from wikidata for {id}: {e.__class__.__name__} | {e}")
        return UNKNOWN_POSTER

    @classmethod
    def get_search_results(cls, title: str) -> list[dict[str, Any]]:
        try:
            return ScrapeClient.get_search_results(title)
        except Exception as e:
            logger.warning(
                f"[MovieClient] Failed to scrape search results from imdb for title '{title}': {e.__class__.__name__} | {e}"
            )
        try:
            return WikidataClient.get_search_results(title)
        except Exception as e:
            logger.warning(
                f"[MovieClient] Failed to fetch search results for {title} from wikidata: {e.__class__.__name__} | {e}"
            )
        return []
