from typing import Any

from const import UNKNOWN_POSTER
from services.api_client import ApiClient
from services.fmdb_client import FmdbClient
from services.imdbdev_client import ImdbdevClient
from services.logger import logger
from services.scrape_client import ScrapeClient


class MovieClient(ApiClient):
    """
    This client provides logic to search movies using several APIs with fallbacks
    """

    BASE_URL = "https://imdb.iamidiotareyoutoo.com"

    @classmethod
    def search_media(cls, title: str):
        try:
            return FmdbClient.search_media(title)
        except Exception as e:
            logger.warning(
                f"[MovieClient] Failed to search for movie using fm-db api with title {title}: {e.__class__.__name__} | {e}"
            )
        try:
            return ImdbdevClient.search_media(title)
        except Exception as e:
            logger.warning(
                f"[MovieClient] Failed to search for movie using imdb.dev with title {title}: {e.__class__.__name__} | {e}"
            )
        try:
            return ScrapeClient.search_media(title)
        except Exception as e:
            logger.warning(
                f"[MovieClient] Failed to search for movie by scraping imdb with title {title}: {e.__class__.__name__} | {e}"
            )
            raise

    @classmethod
    def get_media(cls, id: str, title: str | None = None, **kwargs):
        """
        Fetch media data by ID.

        Tries to fetch data using the fm-db api.
        If it fails, it will try to fetch data using the imdb.dev api.
        If that also fails, tries to scrape the data directly from imdb.
        If that fails too, tries to fetch limited data using another fm-db api endpoint that allows searching by title, if the title is provided.
        When all else fails, returns an empty dict.
        """
        try:
            return FmdbClient.get_media(id, title)
        except Exception as e:
            logger.warning(f"[MovieClient] Failed to fetch data with fm-db api for {id}: {e.__class__.__name__} | {e}")
        try:
            return ImdbdevClient.format_for_movie(ImdbdevClient.get_media(id, **kwargs))
        except Exception as e:
            logger.warning(
                f"[MovieClient] Failed to fetch data with imdb.dev api for {id}: {e.__class__.__name__} | {e}"
            )
        try:
            return ScrapeClient.format_for_movie(ScrapeClient.get_media(id, **kwargs))
        except Exception as e:
            logger.warning(
                f"[MovieClient] Failed to scrape data from imdb for {id}: {e.__class__.__name__} | {e}"
            )
        if title:
            try:
                return FmdbClient.get_media_by_title(title)
            except Exception as e:
                logger.warning(
                    f"[MovieClient] Failed to fetch data for title {title}: {e.__class__.__name__} | {e}"
                )
        return {}

    @classmethod
    def get_poster(cls, id: str, title: str | None = None, **kwargs):  # noqa: ARG003
        """
        Fetch the poster for a movie by its ID.

        Tries to fetch the poster using the fm-db api.
        If it fails, it will try to fetch the poster by title using another fm-db api endpoint, if the title is provided.
        If it fails, it will try to fetch the poster using the imdb.dev api.
        If it fails, it will try to scrape it directly from imdb.
        When all else fails, returns a default unknown poster image.
        """
        try:
            return FmdbClient.get_poster(id)
        except Exception as e:
            logger.warning(
                f"[MovieClient] Failed to fetch poster with fm-db api for {id}: {e.__class__.__name__} | {e}"
            )
        if title:
            try:
                return FmdbClient.get_poster_by_title(title)
            except Exception as e:
                logger.warning(
                    f"[MovieClient] Failed to fetch poster by title {title}: {e.__class__.__name__} | {e}"
                )
        try:
            return ImdbdevClient.get_poster(id)
        except Exception as e:
            logger.warning(
                f"[MovieClient] Failed to fetch poster with imdb.dev api for {id}: {e.__class__.__name__} | {e}"
            )
        try:
            return ScrapeClient.get_poster(id)
        except Exception as e:
            logger.warning(
                f"[MovieClient] Failed to scrape poster from imdb for {id}: {e.__class__.__name__} | {e}"
            )
        return UNKNOWN_POSTER

    @classmethod
    def get_search_results(cls, title: str) -> list[dict[str, Any]]:
        try:
            return FmdbClient.get_search_results(title)
        except Exception as e:
            logger.warning(
                f"[MovieClient] Failed to fetch search results for {title} with fm-db api: {e.__class__.__name__} | {e}"
            )
        try:
            return ImdbdevClient.get_search_results(title)
        except Exception as e:
            logger.warning(
                f"[MovieClient] Failed to fetch search results using imdb.dev for title '{title}': {e.__class__.__name__} | {e}"
            )
        try:
            return ScrapeClient.get_search_results(title)
        except Exception as e:
            logger.warning(
                f"[MovieClient] Failed to scrape search results from imdb for title '{title}': {e.__class__.__name__} | {e}"
            )
        return []
