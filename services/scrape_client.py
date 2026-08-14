import atexit
import io
import json
import os
import re
import threading
import time
from typing import Any
from urllib.parse import quote

from bs4 import BeautifulSoup
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chromium.options import ChromiumOptions
from selenium.webdriver.chromium.webdriver import ChromiumDriver
from selenium.webdriver.edge.options import Options as EdgeOptions

from services.api_client import ApiClient, MediaId
from services.logger import logger

# A plausible headful chrome UA is required: headless chrome's default UA
# contains "HeadlessChrome" and gets hard-blocked (403) by the WAF.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
CHALLENGE_MARKERS = ("awsWafCookieDomainList", "Human Verification")
HELIUM_BINARY = os.path.expandvars(r"%LOCALAPPDATA%\imput\Helium\Application\chrome.exe")

PAGE_LOAD_TIMEOUT = 60
POLL_INTERVAL = 1.5


class ScrapeClient(ApiClient):
    """
    A client that scrapes data directly from the imdb website.

    Imdb is protected by an AWS WAF that requires solving a javascript challenge,
    so pages are fetched with a headless browser using Selenium.
    Used as a last resort fallback when the free api clients fail.

    Poster images are downloaded from m.media-amazon.com, which is not
    protected by the WAF, so plain requests work there.
    """

    BASE_URL = "https://www.imdb.com"

    _driver: Any | None = None
    _driver_lock = threading.Lock()

    @classmethod
    def search_media(cls, title: str) -> str:
        logger.debug(f"[Scrape] Searching for media with title: {title}")
        return cls.get_search_results(title)[0]["id"]

    @classmethod
    def get_media(cls, id: MediaId, **kwargs) -> dict[str, Any]:  # noqa: ARG003
        logger.debug(f"[Scrape] Getting media with id: {id}")
        html = cls._fetch_html(f"{cls.BASE_URL}/title/{id}/")
        data = cls._extract_json_ld(html)
        data.update(cls._extract_page_info(html))
        return data

    @classmethod
    def get_poster(cls, id: MediaId, **kwargs) -> Image.Image:  # noqa: ARG003
        logger.debug(f"[Scrape] Getting poster for media with id: {id}")
        html = cls._fetch_html(f"{cls.BASE_URL}/title/{id}/")
        soup = BeautifulSoup(html, "lxml")
        meta = soup.find("meta", {"property": "og:image"})
        poster_url = meta.get("content") if meta else None
        if not poster_url:
            data = cls._extract_json_ld(html)
            poster_url = data.get("image")
        if not poster_url:
            raise ValueError(f"Could not find a poster url for {id}")
        response = cls.session.get(str(poster_url))
        image = Image.open(io.BytesIO(response.content))
        image.thumbnail((300, 440))
        return image.convert("RGB")

    @classmethod
    def get_search_results(cls, title: str) -> list[dict[str, Any]]:
        logger.debug(f"[Scrape] Getting search results for title: {title}")
        html = cls._fetch_html(f"{cls.BASE_URL}/find/?q={quote(title)}&s=tt&ttype=tt")
        soup = BeautifulSoup(html, "lxml")
        search_results = []
        for link in soup.select("a.ipc-title-link-wrapper"):
            href = str(link.get("href", ""))
            match = re.search(r"/title/(tt\d+)/", href)
            if not match:
                continue
            title_id = match.group(1)
            title_element = link.select_one("h4.ipc-title__text")
            name = title_element.get_text(strip=True) if title_element else link.get_text(strip=True)
            year_element = link.find_next("li", class_="ipc-inline-list__item")
            year = year_element.get_text(strip=True) if year_element else "N/A"
            search_results.append(
                {
                    "name": name,
                    "year": year,
                    "id": title_id,
                    "imdb_url": f"{cls.BASE_URL}/title/{title_id}/",
                }
            )
        if not search_results:
            raise ValueError(f"No results found for title {title}")
        return search_results

    @staticmethod
    def format_for_movie(data: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": data["name"],
            "description": data.get("description", "No description available."),
            "aggregateRating": {"ratingValue": data.get("aggregateRating", {}).get("ratingValue", 0)},
            "duration": ScrapeClient._iso_duration_to_minutes(data.get("duration", "PT0H0M")),
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

    @staticmethod
    def _extract_json_ld(html: str) -> dict[str, Any]:
        soup = BeautifulSoup(html, "lxml")
        for script in soup.find_all("script", {"type": "application/ld+json"}):
            try:
                data = json.loads(script.get_text())
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict) and data.get("name"):
                return data
        raise ValueError("Could not find JSON-LD data in page")

    @staticmethod
    def _extract_page_info(html: str) -> dict[str, Any]:
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
        if not match:
            return {}
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            return {}
        page_props = data.get("props", {}).get("pageProps", {})
        above = page_props.get("aboveTheFoldData") or {}
        info: dict[str, Any] = {}
        name = above.get("titleText", {}).get("text")
        if name:
            info["name"] = name
        episodes = page_props.get("mainColumnData", {}).get("episodes") or {}
        total = episodes.get("totalEpisodes", {}).get("total")
        if total is not None:
            info["episodes"] = int(total)
        season_edges = episodes.get("displayableSeasons", {}).get("edges")
        if season_edges:
            info["seasons"] = len(season_edges)
        elif isinstance(episodes.get("seasons"), list):
            info["seasons"] = len(episodes["seasons"])
        return info

    @staticmethod
    def _iso_duration_to_minutes(duration: str | int | None) -> int:
        if duration is None:
            return 0
        if isinstance(duration, int):
            return duration // 60 if duration >= 3600 else duration
        match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
        if not match:
            return 0
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return (hours * 60) + minutes + (1 if seconds >= 30 else 0)

    @classmethod
    def _fetch_html(cls, url: str) -> str:
        driver = cls._get_driver()
        with cls._driver_lock:
            try:
                driver.get(url)
            except Exception as e:
                raise ValueError(f"Failed to load {url}: {e.__class__.__name__} | {e}") from e
            return cls._wait_for_page(driver, url)

    @classmethod
    def _wait_for_page(cls, driver, url: str) -> str:
        deadline = time.time() + PAGE_LOAD_TIMEOUT
        while time.time() < deadline:
            try:
                html = driver.page_source
            except Exception:
                time.sleep(POLL_INTERVAL)
                continue
            if any(marker in html for marker in CHALLENGE_MARKERS):
                time.sleep(POLL_INTERVAL)
                continue
            return html
        raise TimeoutError(f"Timed out waiting for page to load past the WAF challenge: {url}")

    @classmethod
    def _get_driver(cls):
        if cls._driver is None:
            with cls._driver_lock:
                if cls._driver is None:
                    cls._driver = cls._create_driver()
        return cls._driver

    @classmethod
    def _create_driver(cls):
        webdrivers_list: list[tuple[type[ChromiumOptions], type[ChromiumDriver], str]] = [
            (ChromeOptions, webdriver.Chrome, "chrome"),
            (EdgeOptions, webdriver.Edge, "edge"),
        ]

        for options_class, driver_class, browser_name in webdrivers_list:
            options = options_class()
            if browser_name == "chrome" and os.path.isfile(HELIUM_BINARY):
                options.binary_location = HELIUM_BINARY
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1280,900")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument(f"--user-agent={USER_AGENT}")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            try:
                driver = driver_class(options=options)  # type: ignore
                logger.debug(f"[Scrape] Created headless {browser_name} driver")
                return driver
            except Exception as e:
                logger.warning(f"[Scrape] Failed to create {browser_name} driver: {e.__class__.__name__} | {e}")
        raise OSError("No supported browser found to scrape imdb")

    @classmethod
    def quit(cls):
        with cls._driver_lock:
            if cls._driver is None:
                return
            try:
                cls._driver.quit()
                logger.debug("[Scrape] Closed the browser driver")
            except Exception as e:
                logger.warning(f"[Scrape] Failed to close the browser driver: {e.__class__.__name__} | {e}")
            cls._driver = None


atexit.register(ScrapeClient.quit)
