from typing import Any

from const import UNKNOWN_POSTER
from services.api_client import ApiClient
from services.imdbdev_client import ImdbdevClient
from services.logger import logger
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
                imdb_id = ImdbdevClient.search_media(title)
            except Exception as e:
                logger.warning(
                    f"[ShowClient] Failed to search for show using imdb.dev with title {title}: {e.__class__.__name__} | {e}"
                )

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
                tvmaze_data = TvmazeClient.get_media(tvmaze_id)
            except Exception as e:
                logger.warning(
                    f"[ShowClient] Failed to fetch data using tvmaze for {tvmaze_id}: {e.__class__.__name__} | {e}"
                )

        if imdb_id:
            try:
                logger.debug(f"[ShowClient] Getting show with id: {imdb_id} using imdbdev")
                imdb_data = ImdbdevClient.get_media(imdb_id, **kwargs)
                imdb_data = ImdbdevClient.format_for_show(imdb_data)
                if tvmaze_data:
                    tvmaze_data["rating"] = imdb_data["rating"]
            except Exception as e:
                logger.warning(
                    f"[ShowClient] Failed to fetch data using imdb.dev for {imdb_id}: {e.__class__.__name__} | {e}"
                )

        return tvmaze_data or imdb_data or {}

    @classmethod
    def get_poster(cls, id: tuple[str | None, str | None], **kwargs):  # noqa: ARG003
        tvmaze_id, imdb_id = id

        if tvmaze_id:
            try:
                return TvmazeClient.get_poster(tvmaze_id)
            except Exception as e:
                logger.warning(
                    f"[ShowClient] Failed to fetch poster with tvmaze for {tvmaze_id}: {e.__class__.__name__} | {e}"
                )

        if imdb_id:
            try:
                logger.debug(f"[ShowClient] Getting poster for show with id: {imdb_id} using imdbdev")
                return ImdbdevClient.get_poster(imdb_id)
            except Exception as e:
                logger.warning(
                    f"[ShowClient] Failed to fetch poster with imdb.dev for {imdb_id}: {e.__class__.__name__} | {e}"
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
                imdb_dev_results = ImdbdevClient.get_search_results(title)
                for result in imdb_dev_results:
                    result["id"] = (None, result["id"])
                return imdb_dev_results
            except Exception as e:
                logger.warning(
                    f"[ShowClient] Failed to fetch search results using imdb.dev for title '{title}': {e.__class__.__name__} | {e}"
                )
                return []
