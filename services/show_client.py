from typing import Any

from const import UNKNOWN_POSTER
from services.api_client import ApiClient, MediaId
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

        if not tvmaze_id and not imdb_id:
            raise ValueError(f"Failed to find show with title {title} on tvmaze")
        return tvmaze_id, imdb_id

    @classmethod
    def get_media(cls, id: MediaId, **kwargs) -> dict[str, Any]:  # noqa: ARG003
        if isinstance(id, tuple):
            tvmaze_id = id[0]
        else:
            tvmaze_id = id
        tvmaze_data = None

        if tvmaze_id:
            try:
                tvmaze_data = TvmazeClient.get_media(tvmaze_id)
            except Exception as e:
                logger.warning(
                    f"[ShowClient] Failed to fetch data using tvmaze for {tvmaze_id}: {e.__class__.__name__} | {e}"
                )

        if tvmaze_data:
            # TODO: show ratings should come from imdb, not tvmaze. for now they are always 0.
            tvmaze_data["rating"] = {"average": 0}

        return tvmaze_data or {}

    @classmethod
    def get_poster(cls, id: MediaId, **kwargs):  # noqa: ARG003
        if isinstance(id, tuple):
            tvmaze_id = id[0]
        else:
            tvmaze_id = id

        if tvmaze_id:
            try:
                return TvmazeClient.get_poster(tvmaze_id)
            except Exception as e:
                logger.warning(
                    f"[ShowClient] Failed to fetch poster with tvmaze for {tvmaze_id}: {e.__class__.__name__} | {e}"
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
            return []
