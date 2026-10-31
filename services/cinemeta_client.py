import io
import re
from typing import Any, Literal
from urllib.parse import quote

from PIL import Image

from services.api_client import ApiClient, MediaId, SearchResult
from services.logger import logger

REQUEST_TIMEOUT = 20
MediaType = Literal["movie", "series"]


class CinemetaClient(ApiClient):
    BASE_URL = "https://v3-cinemeta.strem.io"

    @classmethod
    def search_media(cls, title: str, media_type: MediaType) -> str:  # type: ignore[override]
        results = cls.get_search_results(title, media_type)
        for result in results:
            if isinstance(result.id, str) and result.id.startswith("tt"):
                return result.id
        raise ValueError(f"No cinemeta results for {title}")

    @classmethod
    def get_media(cls, id: MediaId, title: str | None = None, **kwargs: Any) -> dict[str, Any]:
        logger.debug(f"[Cinemeta] Getting media with id: {id}")
        meta = cls._fetch_meta(str(id), kwargs["media_type"])
        return {
            "name": meta.get("name", ""),
            "description": meta.get("description", ""),
            "aggregateRating": {"ratingValue": cls._parse_rating(meta.get("imdbRating"))},
            "duration": cls._parse_runtime(meta.get("runtime")),
            "datePublished": cls._parse_date(meta),
        }

    @classmethod
    def get_poster(cls, id: MediaId, title: str | None = None, **kwargs: Any) -> Image.Image:
        logger.debug(f"[Cinemeta] Getting poster for media with id: {id}")
        meta = cls._fetch_meta(str(id), kwargs["media_type"])
        for key in ("poster", "background", "logo"):
            url = meta.get(key)
            if not url:
                continue
            try:
                response = cls.get(url, no_base_url=True, timeout=REQUEST_TIMEOUT)
                image = Image.open(io.BytesIO(response.content))
                image.thumbnail((300, 440))
                return image.convert("RGB")
            except Exception:
                continue
        raise ValueError(f"Could not find a poster for {id} on cinemeta")

    @classmethod
    def get_search_results(cls, title: str, media_type: MediaType, **kwargs: Any) -> list[SearchResult]:  # type: ignore[override]
        logger.debug(f"[Cinemeta] Getting search results for title: {title}")
        results: list[SearchResult] = []
        query = quote(title)
        response = cls.get(
            f"catalog/{media_type}/top/search={query}.json",
            timeout=REQUEST_TIMEOUT,
        )
        metas = response.json().get("metas", [])
        for meta in metas:
            if not cls._matches(meta.get("name", ""), title):
                continue
            imdb_id = meta.get("imdb_id") or meta.get("id", "")
            if not imdb_id:
                continue
            year = str(meta.get("year") or meta.get("releaseInfo") or "N/A")
            results.append(
                SearchResult.model_validate(
                    {
                        "name": meta.get("name", ""),
                        "year": year,
                        "id": imdb_id,
                        "imdb_url": f"https://www.imdb.com/title/{imdb_id}/",
                    }
                )
            )
            if len(results) >= 10:
                break
        if not results:
            raise ValueError(f"No cinemeta results for {title}")
        return results

    @classmethod
    def get_show_counts(cls, id: MediaId) -> tuple[int, int]:
        try:
            meta = cls._fetch_meta(str(id), "series")
        except Exception:
            return 0, 0
        videos = meta.get("videos") or []
        seasons: set[int] = set()
        episode_count = 0
        for video in videos:
            if not isinstance(video, dict):
                continue
            season = video.get("season")
            # season 0 = specials/extras, not a real season
            if isinstance(season, int) and season > 0:
                seasons.add(season)
                episode_count += 1
        return episode_count, (max(seasons) if seasons else 0)

    @classmethod
    def _fetch_meta(cls, imdb_id: str, media_type: MediaType) -> dict[str, Any]:
        meta = cls.get(f"meta/{media_type}/{imdb_id}.json", timeout=REQUEST_TIMEOUT).json().get("meta")
        if meta or not meta.get("name"):
            raise ValueError(f"Could not fetch cinemeta meta for {imdb_id}")
        return meta

    @staticmethod
    def _matches(candidate: str, query: str) -> bool:
        tokens = [t for t in re.split(r"[^a-z0-9]+", query.lower()) if len(t) > 2]
        lowered = candidate.lower()
        return bool(tokens) and any(t in lowered for t in tokens)

    @staticmethod
    def _parse_rating(value: Any) -> float:
        if not value:
            return 0
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _parse_runtime(value: Any) -> int:
        match = re.search(r"(\d+)\s*min", str(value))
        return int(match.group(1)) if match else 0

    @staticmethod
    def _parse_date(meta: dict[str, Any]) -> str:
        for key in ("released", "dvdRelease"):
            released = meta.get(key)
            if released:
                return released[:10]
        year = str(meta.get("year") or meta.get("releaseInfo") or "")
        match = re.match(r"\d{4}", year)
        return f"{match.group()}-00-00" if match else "0000-00-00"
