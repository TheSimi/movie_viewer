from typing import Any

from const import UNKNOWN_POSTER
from services.api_client import ApiClient, MediaId
from services.logger import logger
from services.scrape_client import ScrapeClient
from services.tvmaze_client import TvmazeClient


class ShowClient(ApiClient):
    BASE_URL = "https://api.tvmaze.com"

    @classmethod
    def search_media(cls, title: str) -> tuple[str | None, str | None]:
        try:
            tvmaze_id, imdb_id = TvmazeClient.search_media(title)
        except Exception as e:
            logger.warning(f"[Tvmaze] Failed to search for show with title {title}: {e.__class__.__name__} | {e}")
            tvmaze_id, imdb_id = None, None

        if not imdb_id:
            try:
                imdb_id = ScrapeClient.search_media(title)
            except Exception as e:
                logger.warning(
                    f"[ShowClient] Failed to search for show by scraping imdb with title {title}: {e.__class__.__name__} | {e}"
                )

        if not tvmaze_id and not imdb_id:
            raise ValueError(f"Failed to find show with title {title} on both tvmaze and imdb scrape")
        return tvmaze_id, imdb_id

    @classmethod
    def get_media(cls, id: MediaId, **kwargs) -> dict[str, Any]:
        if isinstance(id, tuple):
            tvmaze_id, imdb_id = id
        else:
            tvmaze_id, imdb_id = id, None
        tvmaze_data = None
        imdb_data = None

        if tvmaze_id:
            try:
                tvmaze_data = TvmazeClient.get_media(tvmaze_id)
            except Exception as e:
                logger.warning(
                    f"[ShowClient] Failed to fetch data using tvmaze for {tvmaze_id}: {e.__class__.__name__} | {e}"
                )

        if imdb_id:
            try:
                imdb_data = ScrapeClient.format_for_show(ScrapeClient.get_media(imdb_id, **kwargs))
            except Exception as e:
                logger.warning(
                    f"[ShowClient] Failed to scrape data from imdb for {imdb_id}: {e.__class__.__name__} | {e}"
                )

        if tvmaze_data:
            if imdb_data:
                tvmaze_data["rating"] = imdb_data.get("rating", 0)
            else:
                # TODO: rating is 0 when the imdb rating could not be scraped, might want a better fallback
                tvmaze_data["rating"] = {"average": 0}

        return tvmaze_data or imdb_data or {}

    @classmethod
    def get_poster(cls, id: MediaId, **kwargs):  # noqa: ARG003
        if isinstance(id, tuple):
            tvmaze_id, imdb_id = id
        else:
            tvmaze_id, imdb_id = id, None

        if tvmaze_id:
            try:
                return TvmazeClient.get_poster(tvmaze_id)
            except Exception as e:
                logger.warning(
                    f"[ShowClient] Failed to fetch poster with tvmaze for {tvmaze_id}: {e.__class__.__name__} | {e}"
                )

        if imdb_id:
            try:
                return ScrapeClient.get_poster(imdb_id)
            except Exception as e:
                logger.warning(
                    f"[ShowClient] Failed to scrape poster from imdb for {imdb_id}: {e.__class__.__name__} | {e}"
                )

        return UNKNOWN_POSTER

    @classmethod
    def get_search_results(cls, title: str) -> list[dict[str, Any]]:
        try:
            return TvmazeClient.get_search_results(title)
        except Exception as e:
            logger.warning(
                f"[ShowClient] Failed to fetch search results for {title} with tvmaze: {e.__class__.__name__} | {e}"
            )
        try:
            scrape_results = ScrapeClient.get_search_results(title)
            for result in scrape_results:
                result["id"] = (None, result["id"])
            return scrape_results
        except Exception as e:
            logger.warning(
                f"[ShowClient] Failed to scrape search results from imdb for title '{title}': {e.__class__.__name__} | {e}"
            )
            return []
