import io
import re
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from typing import Any
from urllib.parse import quote

import requests
from PIL import Image
from requests import Session

from services.api_client import ApiClient, MediaId
from services.logger import logger

try:
    _requests_version = package_version("requests")
except PackageNotFoundError:
    # importlib.metadata has no package metadata in frozen (PyInstaller) builds
    _requests_version = getattr(requests, "__version__", "unknown")

USER_AGENT = f"WikidataFetcher/1.0 python-requests/{_requests_version}"

REQUEST_TIMEOUT = 15
MAX_RESULTS = 10

# instance of: film, short film, TV film
FILM_TYPE_IDS = frozenset({11424, 24862, 50624072})
YEAR_PATTERN = re.compile(r"\b(?:19|20)\d{2}\b")
DISAMBIGUATION_PATTERN = re.compile(r"\s+\(\d{4}(?: film)?\)$")


class WikidataClient(ApiClient):
    BASE_URL = "https://www.wikidata.org/w"
    COMMONS_BASE_URL = "https://commons.wikimedia.org/w"

    session = Session()
    session.headers.update({"User-Agent": USER_AGENT})

    @classmethod
    def search_media(cls, title: str) -> str:
        logger.debug(f"[Wikidata] Searching for movie with title: {title}")
        entity = cls._get_best_entity(title)
        imdb_id = entity["imdb_id"]
        if not imdb_id:
            raise ValueError(f"Could not find an imdb id for {title} on wikidata")
        return imdb_id

    @classmethod
    def get_media(cls, id: MediaId, title: str | None = None, **kwargs) -> dict[str, Any]:  # noqa: ARG003
        logger.debug(f"[Wikidata] Getting movie with id: {id}")
        entity = cls._find_entity(id, title)
        return {
            "name": entity["name"],
            "description": "",
            "aggregateRating": {"ratingValue": 0},
            "duration": entity["duration"] or 0,
            "datePublished": entity["date_published"],
        }

    @classmethod
    def get_poster(cls, id: MediaId, title: str | None = None, **kwargs) -> Image.Image:  # noqa: ARG003
        logger.debug(f"[Wikidata] Getting poster for movie with id: {id}")
        entity = cls._find_entity(id, title)
        if not entity["images"]:
            raise ValueError(f"Could not find a poster image for {entity['name']} on wikidata")
        file_name = cls._pick_poster(entity["images"])
        url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{quote(file_name.replace(' ', '_'))}?width=300"
        response = cls.session.get(url, timeout=REQUEST_TIMEOUT)
        image = Image.open(io.BytesIO(response.content))
        image.thumbnail((300, 440))
        return image.convert("RGB")

    @classmethod
    def get_search_results(cls, title: str) -> list[dict[str, Any]]:
        logger.debug(f"[Wikidata] Getting search results for title: {title}")
        search_results = []
        for entity in cls._get_entities(title):
            imdb_id = entity["imdb_id"]
            if not imdb_id:
                continue
            search_results.append(
                {
                    "name": entity["name"],
                    "year": entity["year"] or "",
                    "id": imdb_id,
                    "imdb_url": f"https://www.imdb.com/title/{imdb_id}",
                }
            )
        return search_results

    @classmethod
    def _get_best_entity(cls, title: str) -> dict[str, Any]:
        entities = cls._get_entities(title)
        if not entities:
            raise ValueError(f"Could not find any film for {title} on wikidata")
        year = cls._extract_year(title)
        if year is not None:
            for entity in entities:
                if entity["year"] == year:
                    return entity
        return entities[0]

    @classmethod
    def _get_entities(cls, title: str) -> list[dict[str, Any]]:
        ids = cls._search_entity_ids(title)
        if not ids:
            return []
        entities = cls._get_entities_data(ids)
        parsed_entities = []
        for entity_id in ids:
            entity = entities.get(entity_id)
            if entity is None or not cls._is_film(entity):
                continue
            parsed_entities.append(cls._parse_entity(entity))
        return parsed_entities

    @classmethod
    def _search_entity_ids(cls, title: str) -> list[str]:
        response = cls.get(
            "api.php",
            params={
                "action": "query",
                "list": "search",
                "format": "json",
                "srsearch": f"{title} haswbstatement:P31=Q11424",
                "srlimit": MAX_RESULTS,
            },
            timeout=REQUEST_TIMEOUT,
        )
        hits = response.json().get("query", {}).get("search", [])
        ids = [hit["title"] for hit in hits if re.fullmatch(r"Q\d+", hit["title"])]
        if ids:
            return ids
        # fall back to the search entities endpoint in case cirrussearch missed something
        search_title = cls._strip_year(title)
        response = cls.get(
            "api.php",
            params={
                "action": "wbsearchentities",
                "format": "json",
                "language": "en",
                "type": "item",
                "limit": MAX_RESULTS,
                "search": search_title,
            },
            timeout=REQUEST_TIMEOUT,
        )
        return [result["id"] for result in response.json().get("search", [])]

    @classmethod
    def _get_entities_data(cls, ids: list[str]) -> dict[str, Any]:
        response = cls.get(
            "api.php",
            params={
                "action": "wbgetentities",
                "format": "json",
                "languages": "en",
                "props": "labels|claims",
                "ids": "|".join(ids),
            },
            timeout=REQUEST_TIMEOUT,
        )
        return response.json().get("entities", {})

    @classmethod
    def _find_entity(cls, id: MediaId, title: str | None) -> dict[str, Any]:
        if title:
            return cls._get_best_entity(title)
        if isinstance(id, str) and id.startswith("tt"):
            return cls._get_entity_by_imdb_id(id)
        raise ValueError(f"Could not find a wikidata entity for {id} without a title")

    @classmethod
    def _get_entity_by_imdb_id(cls, imdb_id: str) -> dict[str, Any]:
        response = cls.get(
            "api.php",
            params={
                "action": "query",
                "list": "search",
                "format": "json",
                "srsearch": f"haswbstatement:P345={imdb_id}",
                "srlimit": 1,
            },
            timeout=REQUEST_TIMEOUT,
        )
        hits = response.json().get("query", {}).get("search", [])
        if not hits:
            raise ValueError(f"Could not find a wikidata entity for imdb id {imdb_id}")
        entity_id = hits[0]["title"]
        entity = cls._get_entities_data([entity_id]).get(entity_id)
        if entity is None:
            raise ValueError(f"Could not load wikidata entity {entity_id}")
        return cls._parse_entity(entity)

    @classmethod
    def _pick_poster(cls, images: list[str]) -> str:
        response = cls.session.get(
            f"{cls.COMMONS_BASE_URL}/api.php",
            params={
                "action": "query",
                "format": "json",
                "titles": "|".join(f"File:{image}" for image in images),
                "prop": "imageinfo",
                "iiprop": "size",
            },
            timeout=REQUEST_TIMEOUT,
        )
        sizes: dict[str, tuple[int, int]] = {}
        for page in response.json().get("query", {}).get("pages", {}).values():
            info = page.get("imageinfo")
            if info:
                file_name = str(page["title"]).removeprefix("File:")
                sizes[file_name] = (info[0]["width"], info[0]["height"])
        for image in images:
            width, height = sizes.get(image, (0, 0))
            if height > width:
                return image
        return images[0]

    @staticmethod
    def _is_film(entity: dict[str, Any]) -> bool:
        for claim in entity.get("claims", {}).get("P31", []):
            datavalue = claim.get("mainsnak", {}).get("datavalue")
            value = datavalue.get("value", {}) if datavalue else {}
            if value.get("numeric-id") in FILM_TYPE_IDS:
                return True
        return False

    @classmethod
    def _parse_entity(cls, entity: dict[str, Any]) -> dict[str, Any]:
        label = entity.get("labels", {}).get("en", {}).get("value", entity.get("id", ""))
        claims = entity.get("claims", {})

        def claim_values(prop: str) -> list[Any]:
            values = []
            for claim in claims.get(prop, []):
                datavalue = claim.get("mainsnak", {}).get("datavalue")
                if datavalue:
                    values.append(datavalue["value"])
            return values

        imdb_id = next((v for v in claim_values("P345") if isinstance(v, str)), None)
        dates = [v["time"] for v in claim_values("P577") if isinstance(v, dict) and v.get("time")]
        images = [v for v in claim_values("P18") if isinstance(v, str)]
        titles = [v["text"] for v in claim_values("P1476") if isinstance(v, dict) and v.get("text")]

        duration = None
        for value in claim_values("P2047"):
            if isinstance(value, dict) and isinstance(value.get("amount"), str):
                try:
                    duration = int(value["amount"].lstrip("+"))
                except ValueError:
                    pass
                break

        name = cls._clean_title(label) or (titles[0] if titles else label)
        return {
            "name": name,
            "imdb_id": imdb_id,
            "year": cls._year_from_dates(dates),
            "date_published": cls._format_date(dates),
            "duration": duration,
            "images": images,
        }

    @staticmethod
    def _year_from_dates(dates: list[str]) -> int | None:
        years = []
        for date in dates:
            match = re.match(r"\+(\d{4})", date)
            if match:
                years.append(int(match.group(1)))
        return min(years) if years else None

    @staticmethod
    def _format_date(dates: list[str]) -> str:
        if not dates:
            return "0000-00-00"
        full_dates = sorted(
            date for date in dates if re.fullmatch(r"\+\d{4}-\d{2}-\d{2}T.*", date) and "-00-" not in date[1:11]
        )
        if full_dates:
            return full_dates[0][1:11]
        year_only = sorted(date for date in dates if re.match(r"\+(\d{4})", date))
        if year_only:
            return f"{year_only[0][1:5]}-00-00"
        return "0000-00-00"

    @staticmethod
    def _clean_title(label: str) -> str:
        return DISAMBIGUATION_PATTERN.sub("", label).strip()

    @staticmethod
    def _extract_year(title: str) -> int | None:
        match = YEAR_PATTERN.search(title)
        return int(match.group(0)) if match else None

    @classmethod
    def _strip_year(cls, title: str) -> str:
        year = cls._extract_year(title)
        if year is None:
            return title
        stripped = YEAR_PATTERN.sub("", title).strip(" ()-.")
        return stripped or title
