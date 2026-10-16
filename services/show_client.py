import os
from typing import Any

from PIL import Image

from const import UNKNOWN_POSTER
from media_classes.show import Show
from services.api_client import ApiClient, MediaId, SearchResult
from services.logger import logger
from services.scrape_client import ScrapeClient
from services.tvmaze_client import TvmazeClient


class ShowClient(ApiClient):
    BASE_URL = "https://api.tvmaze.com"

    @classmethod
    def search_media(cls, title: str) -> tuple[str | int | None, str | None]:
        # Unlike other methods we use tvmaze by default here
        # since it returns both the tvmaze id and the imdb id,
        # and both are needed downstream.
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
    def fetch_media_data(cls, id: MediaId, **kwargs: Any) -> dict[str, Any]:
        """
        Fetch raw show dict (imdb scrape -> tvmaze fallback).
        """
        tvmaze_id, imdb_id = cls._split_id(id)

        if imdb_id:
            try:
                return ScrapeClient.format_for_show(ScrapeClient.get_media(imdb_id, **kwargs))
            except Exception as e:
                logger.warning(
                    f"[ShowClient] Failed to scrape data from imdb for {imdb_id}: {e.__class__.__name__} | {e}"
                )

        if tvmaze_id:
            try:
                tvmaze_data = TvmazeClient.get_media(tvmaze_id)
                # Only imdb ratings are used, so drop the tvmaze rating.
                tvmaze_data["rating"] = {"average": 0}
                return tvmaze_data
            except Exception as e:
                logger.warning(
                    f"[ShowClient] Failed to fetch data using tvmaze for {tvmaze_id}: {e.__class__.__name__} | {e}"
                )

        return {}

    @classmethod
    def get_media(cls, id: MediaId, title: str | None = None, path: str = "", **kwargs: Any) -> Show:
        """
        Fetch show by ID and return a validated Show model.
        """
        data = cls.fetch_media_data(id, **kwargs)
        try:
            poster = cls.get_poster(id, **kwargs)
        except Exception as e:
            logger.warning(f"[ShowClient] Failed to fetch poster for {id}: {e.__class__.__name__} | {e}")
            poster = UNKNOWN_POSTER.copy()
        fallback_name = title or (os.path.splitext(os.path.basename(path))[0] if path else "")
        return Show.model_validate(
            {
                **data,
                "path": path,
                "id": id,
                "image": poster,
                "name": data.get("name", fallback_name),
            }
        )

    @classmethod
    def get_poster(cls, id: MediaId, **kwargs: Any) -> Image.Image:  # noqa: ARG003
        tvmaze_id, imdb_id = cls._split_id(id)

        if imdb_id:
            try:
                return ScrapeClient.get_poster(imdb_id)
            except Exception as e:
                logger.warning(
                    f"[ShowClient] Failed to scrape poster from imdb for {imdb_id}: {e.__class__.__name__} | {e}"
                )

        if tvmaze_id:
            try:
                return TvmazeClient.get_poster(tvmaze_id)
            except Exception as e:
                logger.warning(
                    f"[ShowClient] Failed to fetch poster with tvmaze for {tvmaze_id}: {e.__class__.__name__} | {e}"
                )

        return UNKNOWN_POSTER.copy()

    @classmethod
    def get_search_results(cls, title: str) -> list[SearchResult]:
        try:
            results = list(ScrapeClient.get_search_results(title))
            for result in results:
                if isinstance(result.id, str):
                    result.id = (None, result.id)
            return results
        except Exception as e:
            logger.warning(
                f"[ShowClient] Failed to scrape search results from imdb for title '{title}': {e.__class__.__name__} | {e}"
            )
        try:
            return list(TvmazeClient.get_search_results(title))
        except Exception as e:
            logger.warning(
                f"[ShowClient] Failed to fetch search results for {title} with tvmaze: {e.__class__.__name__} | {e}"
            )
            return []

    @staticmethod
    def _split_id(id: MediaId) -> tuple[str | int | None, str | None]:
        if isinstance(id, tuple):
            return id
        if isinstance(id, list):
            first = id[0] if len(id) > 0 else None
            second = id[1] if len(id) > 1 else None
            return first, second
        if isinstance(id, str) and id.startswith("tt"):
            return None, id
        return id, None
