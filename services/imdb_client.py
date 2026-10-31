import io
import re
from typing import Any, cast
from urllib.parse import quote

from PIL import Image

from services.api_client import ApiClient, MediaId, SearchResult
from services.logger import logger

# Imdb uses this for it's search
SUGGEST_BASE_URL = "https://v3.sg.media-imdb.com/suggestion"

# Imdb uses this to fetch movie info
GRAPHQL_URL = "https://api.graphql.imdb.com/"

USER_AGENT_HEADER = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
)
GRAPHQL_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": USER_AGENT_HEADER,
    "Origin": "https://www.imdb.com",
    "Referer": "https://www.imdb.com/",
    "Accept-Language": "en-US,en;q=0.9",
}
REQUEST_TIMEOUT = 30

TITLE_DETAILS_QUERY = """
query TitleDetails($id: ID!) {
  title(id: $id) {
    id
    titleText { text }
    titleType { id text }
    releaseYear { year endYear }
    releaseDate { day month year }
    runtime { seconds }
    runtimes(first: 5) { edges { node { seconds } } }
    ratingsSummary { aggregateRating voteCount }
    plot { plotText { plainText } }
    plots(first: 1) { edges { node { plotText { plainText } } } }
    primaryImage { url width height }
  }
}
"""


class IMDbClient(ApiClient):
    BASE_URL = "https://www.imdb.com"

    @classmethod
    def search_media(cls, title: str) -> str:
        logger.debug(f"[IMDb] Searching for media with title: {title}")
        return cast(str, next(iter(cls.get_search_results(title))).id)

    @classmethod
    def get_media(cls, id: MediaId, **kwargs) -> dict[str, Any]:
        logger.debug(f"[IMDb] Getting media with id: {id}")
        data = cls._graphql("TitleDetails", TITLE_DETAILS_QUERY, {"id": str(id)})
        title = (data.get("data") or {}).get("title")
        if not title:
            errors = data.get("errors")
            raise ValueError(f"IMDb GraphQL returned no title for {id}: {errors}")
        return cls._map_title(title, str(id))

    @classmethod
    def get_poster(cls, id: MediaId, **kwargs) -> Image.Image:
        logger.debug(f"[IMDb] Getting poster for media with id: {id}")
        poster_url = None
        try:
            data = cls._graphql("TitleDetails", TITLE_DETAILS_QUERY, {"id": str(id)})
            title = data.get("data", {}).get("title", {})
            image = title.get("primaryImage", {})
            poster_url = image.get("url")
        except Exception as e:
            logger.debug(f"[IMDb] GraphQL poster lookup failed for {id}: {e}")
        if not poster_url:
            raise ValueError(f"Could not find a poster url for {id}")
        response = cls.get(str(poster_url), no_base_url=True, timeout=REQUEST_TIMEOUT)
        image = Image.open(io.BytesIO(response.content))
        image.thumbnail((300, 440))
        return image.convert("RGB")

    @classmethod
    def get_search_results(cls, title: str, **kwargs: Any) -> list[SearchResult]:
        logger.debug(f"[IMDb] Getting search results for title: {title}")
        suggestions = cls._fetch_suggestions(title)
        search_results = []
        for item in suggestions:
            title_id: str = item.get("id", "")
            if not title_id:
                continue
            name = str(item.get("l", "")).strip() or title
            year = item.get("y")
            search_results.append(
                {
                    "name": name,
                    "year": str(year) if year else "N/A",
                    "id": title_id,
                    "imdb_url": f"{cls.BASE_URL}/title/{title_id}/",
                }
            )
        if not search_results:
            raise ValueError(f"No results found for title {title}")
        return [SearchResult.model_validate(item) for item in search_results]

    @staticmethod
    def format_for_movie(data: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": data["name"],
            "description": data.get("description", "No description available."),
            "aggregateRating": {"ratingValue": data.get("aggregateRating", {}).get("ratingValue", 0)},
            "duration": IMDbClient._duration_to_minutes(data.get("duration", "PT0H0M")),
            "datePublished": data.get("datePublished", "0000-00-00"),
        }

    @staticmethod
    def format_for_show(data: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": data["name"],
            "summary": data.get("description", ""),
            "rating": {"average": data.get("aggregateRating", {}).get("ratingValue", 0)},
            "premiered": data.get("datePublished", "0000-00-00"),
            "episodes": int(data.get("episodes") or 0),
            "seasons": int(data.get("seasons") or 0),
        }

    @classmethod
    def _graphql(cls, operation: str, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        response = cls.session.post(
            GRAPHQL_URL,
            json={"query": query, "operationName": operation, "variables": variables},
            headers=GRAPHQL_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    @classmethod
    def _map_title(cls, title: dict[str, Any], imdb_id: str) -> dict[str, Any]:
        name: str = title.get("titleText", {}).get("text") or imdb_id
        rating: float = title.get("ratingsSummary", {}).get("aggregateRating", 0)
        description: str = title.get("plot", {}).get("plotText", {}).get("plainText", "")
        if not description:
            plot_edges: list[dict[str, dict[str, dict[str, str]]]] = title.get("plots", {}).get("edges", [])
            description = next(iter(plot_edges), {}).get("node", {}).get("plotText", {}).get("plainText", "")
        seconds: int = title.get("runtime", {}).get("seconds", 0)
        if not seconds:
            runtime_edges: list[dict[str, int]] = (title.get("runtimes") or {}).get("edges", [])
            seconds = next(iter(runtime_edges), {}).get("seconds", 0)
        release: dict[str, Any] = title.get("releaseDate", {})
        year = release.get("year") or title.get("releaseYear", {}).get("year")
        if release.get("year") and release.get("month") and release.get("day"):
            date_published = f"{release['year']:04d}-{release['month']:02d}-{release['day']:02d}"
        else:
            date_published = f"{int(year):04d}-00-00" if year else "0000-00-00"
        image = title.get("primaryImage", {})
        return {
            "name": name or imdb_id,
            "description": description or "No description available.",
            "aggregateRating": {"ratingValue": rating},
            "duration": cls._seconds_to_minutes(seconds),
            "datePublished": date_published,
            "image": image.get("url"),
            "episodes": 0,
            "seasons": 0,
        }

    @classmethod
    def _fetch_suggestions(cls, title: str) -> list[dict[str, Any]]:
        cleaned = title.strip().lower()
        if not cleaned:
            raise ValueError("Empty title for imdb suggestion search")
        first = cleaned[0] if cleaned[0].isalnum() else "a"
        url = f"{SUGGEST_BASE_URL}/{quote(first)}/{quote(cleaned)}.json"
        response = cls.get(url, no_base_url=True, headers={"User-Agent": USER_AGENT_HEADER}, timeout=REQUEST_TIMEOUT)
        data = response.json()
        items = data.get("d") or []
        return [item for item in items if isinstance(item, dict)]

    @staticmethod
    def _seconds_to_minutes(seconds: Any) -> int:
        try:
            total = int(seconds or 0)
        except (TypeError, ValueError):
            return 0
        return max(0, round(total / 60))

    @staticmethod
    def _duration_to_minutes(duration: str | int | None) -> int:
        if duration is None:
            return 0
        if isinstance(duration, int):
            return duration // 60 if duration >= 3600 else duration
        match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            return (hours * 60) + minutes + (1 if seconds >= 30 else 0)
        try:
            return int(duration)
        except (TypeError, ValueError):
            return 0
