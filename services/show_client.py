import os
from typing import Any

from PIL import Image

from const import UNKNOWN_POSTER
from media_classes.show import Show
from services.api_client import ApiClient, MediaId, SearchResult
from services.cinemeta_client import CinemetaClient
from services.imdb_client import IMDbClient
from services.logger import logger
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
                imdb_id = IMDbClient.search_media(title)
            except Exception as e:
                logger.warning(
                    f"[ShowClient] Failed to search imdb for show with title {title}: {e.__class__.__name__} | {e}"
                )

        if not imdb_id:
            try:
                imdb_id = CinemetaClient.search_media(title, media_type="series")
            except Exception as e:
                logger.warning(
                    f"[ShowClient] Failed to search cinemeta for show with title {title}: {e.__class__.__name__} | {e}"
                )

        if not tvmaze_id and not imdb_id:
            raise ValueError(f"Failed to find show with title {title} on tvmaze, imdb and cinemeta")
        return tvmaze_id, imdb_id

    @classmethod
    def fetch_media_data(cls, id: MediaId, **kwargs: Any) -> dict[str, Any]:
        """
        Fetch raw show dict (imdb -> cinemeta -> tvmaze fallback).
        """
        tvmaze_id, imdb_id = cls._split_id(id)

        imdb_data: dict[str, Any] | None = None
        if imdb_id:
            try:
                imdb_data = IMDbClient.format_for_show(IMDbClient.get_media(imdb_id, **kwargs))
            except Exception as e:
                logger.warning(
                    f"[ShowClient] Failed to fetch data direct from imdb for {imdb_id}: {e.__class__.__name__} | {e}"
                )

        if imdb_id and (not imdb_data or not imdb_data.get("episodes") or not imdb_data.get("seasons")):
            try:
                episodes, seasons = CinemetaClient.get_show_counts(imdb_id)
                if not imdb_data:
                    cinemeta_data = CinemetaClient.get_media(imdb_id, media_type="series")
                    imdb_data = {
                        "name": cinemeta_data.get("name", ""),
                        "summary": cinemeta_data.get("description", ""),
                        "rating": {"average": cinemeta_data.get("aggregateRating", {}).get("ratingValue", 0)},
                        "premiered": cinemeta_data.get("datePublished", "0000-00-00"),
                        "episodes": episodes,
                        "seasons": seasons,
                    }
                elif not imdb_data.get("episodes"):
                    imdb_data["episodes"] = episodes
                elif not imdb_data.get("seasons"):
                    imdb_data["seasons"] = seasons
            except Exception as e:
                logger.warning(
                    f"[ShowClient] Failed to fetch show counts from cinemeta for {imdb_id}: {e.__class__.__name__} | {e}"
                )

        if imdb_data:
            if (not imdb_data.get("episodes") or not imdb_data.get("seasons")) and tvmaze_id:
                try:
                    tvmaze_data = TvmazeClient.get_media(tvmaze_id)
                    embedded = (tvmaze_data.get("_embedded") or {}).get("episodes", [])
                    if embedded:
                        imdb_data["episodes"] = len(embedded)
                        imdb_data["seasons"] = len(
                            {
                                ep.get("season")
                                for ep in embedded
                                if isinstance(ep, dict) and isinstance(ep.get("season"), int)
                            }
                        )
                except Exception as e:
                    logger.warning(
                        f"[ShowClient] Failed to supplement counts from tvmaze for {tvmaze_id}: {e.__class__.__name__} | {e}"
                    )
            return imdb_data

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
    def get_poster(cls, id: MediaId, **kwargs: Any) -> Image.Image:
        tvmaze_id, imdb_id = cls._split_id(id)

        if imdb_id:
            try:
                return IMDbClient.get_poster(imdb_id)
            except Exception as e:
                logger.warning(
                    f"[ShowClient] Failed to fetch poster from imdb for {imdb_id}: {e.__class__.__name__} | {e}"
                )
            try:
                return CinemetaClient.get_poster(imdb_id, media_type="series")
            except Exception as e:
                logger.warning(
                    f"[ShowClient] Failed to fetch poster from cinemeta for {imdb_id}: {e.__class__.__name__} | {e}"
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
    def get_search_results(cls, title: str, **kwargs: Any) -> list[SearchResult]:
        try:
            results = list(IMDbClient.get_search_results(title, **kwargs))
            for result in results:
                if isinstance(result.id, str):
                    result.id = (None, result.id)
            return results
        except Exception as e:
            logger.warning(
                f"[ShowClient] Failed to fetch search results from imdb for title '{title}': {e.__class__.__name__} | {e}"
            )
        try:
            return list(CinemetaClient.get_search_results(title, media_type="series", **kwargs))
        except Exception as e:
            logger.warning(
                f"[ShowClient] Failed to fetch search results for {title} with cinemeta: {e.__class__.__name__} | {e}"
            )
        try:
            return list(TvmazeClient.get_search_results(title, **kwargs))
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
