import abc
from typing import Any

from PIL import Image
from requests import Response, Session
from requests.exceptions import HTTPError

from const import RETRY_AMOUNT
from services.logger import logger

# either just imdb id - e.g tt0133093
# or tuple of (imdb_id, tvmaze_id) - e.g (tt0944947, 82)
MediaId = str | tuple[str | None, str | None]


class ApiClient(abc.ABC):
    BASE_URL: str
    session = Session()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Ensure the subclass isn't just another abstract class
        if abc.abstractmethod not in cls.__dict__.values():
            if not hasattr(cls, "BASE_URL"):
                raise TypeError(f"Class {cls.__name__} must define 'BASE_URL'")

    @classmethod
    def request(cls, method, url, *args, **kwargs) -> Response:
        for attempt in range(RETRY_AMOUNT):
            try:
                full_url = f"{cls.BASE_URL}/{url}"
                logger.debug(f"Request Attemp #{attempt + 1}: {method} {full_url}")
                response = cls.session.request(method, full_url, *args, **kwargs)
                response.raise_for_status()
                return response
            except HTTPError as e:
                logger.error(f"Failed to make request to {url}: {e.response.status_code} | {e.response.text}")
        raise Exception(f"Failed to make request to {url} after {RETRY_AMOUNT} attempts")

    @classmethod
    def get(cls, url, *args, **kwargs) -> Response:
        return cls.request("GET", url, *args, **kwargs)

    @classmethod
    @abc.abstractmethod
    def search_media(cls, title: str) -> MediaId:
        """
        Search for a media and return its id

        :param title: The title of the media
        :type title: str
        :return: The media id
        :rtype: MediaId
        """
        ...

    @classmethod
    @abc.abstractmethod
    def get_media(cls, id: MediaId, **kwargs) -> dict[str, Any]:
        """
        Get a media by it's id

        :param id: The id of the media
        :type id: MediaId
        :return: The media data
        :rtype: dict [str, any]
        """
        ...

    @classmethod
    @abc.abstractmethod
    def get_poster(cls, id: MediaId, **kwargs) -> Image.Image:
        """
        Get a media poster by it's id

        :param id: The id of the media
        :type id: MediaId
        :return: The media poster in a 300x440 resolution
        :rtype: Image.Image
        """
        ...

    @classmethod
    @abc.abstractmethod
    def get_search_results(cls, title: str) -> list[dict[str, Any]]:
        """
        Get search results for a media title

        :param title: The title of the media
        :type title: str
        :return: A list of search results with their data, with these keys:
            - name: The title of the media
            - year: The year of release of the media
            - id: The id of the media
            - imdb_url: The imdb url of the media
        :rtype: list [dict [str, any]]
        """
        ...
