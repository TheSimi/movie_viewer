import io

from PIL import Image

from const import UNKNOWN_POSTER
from services.api_client import ApiClient
from services.imdbdev_client import ImdbdevClient
from services.logger import logger


class MovieClient(ApiClient):
    BASE_URL = "https://imdb.iamidiotareyoutoo.com"

    @classmethod
    def search_media(cls, title: str):
        try:
            logger.debug(f"[FM-DB] Searching for movie with title: {title}")
            return cls.get("search", params={"q": title}).json()["description"][0][
                "#IMDB_ID"
            ]
        except Exception as e:
            logger.warning(
                f"Failed to search for movie using fm-db api with title {title}: {e.__class__.__name__} | {e}"
            )
            return ImdbdevClient.search_media(title)

    @classmethod
    def get_media(cls, id: str, title: str | None = None, **kwargs):
        """
        Fetch media data by ID.

        Tries to fetch data using the fm-db api.
        If it fails, it will try to fetch data using the imdb.dev api.
        If that also fails, tries to fetch limited data using another fm-db api endpoint that allows searching by title, if the title is provided.
        When all else fails, returns an empty dict.
        """
        try:
            logger.debug(f"[FM-DB] Getting movie with id: {id}")
            data = cls.get("search", params={"tt": id}).json()["short"]
            if title:
                media_title = cls.get_media_name(title)
                if media_title:
                    data["name"] = media_title
            return data
        except Exception as e:
            logger.warning(
                f"Failed to fetch data with fm-db api for {id}: {e.__class__.__name__} | {e}"
            )
            try:
                data = ImdbdevClient.get_media(id, **kwargs)
                return ImdbdevClient.format_for_movie(data)
            except Exception as e:
                logger.warning(
                    f"Failed to fetch data with imdb.dev api for {id}: {e.__class__.__name__} | {e}"
                )
                if title:
                    return cls.get_media_by_title(title)
                return {}

    @classmethod
    def get_media_name(cls, title: str) -> str | None:
        """
        Fetch the name of a media item by its title.

        This is used because when dealing with a foriegn movie, the fm-db api returns
        the title in the original language, so we need to make another request to get the english title.
        """
        try:
            logger.debug(f"[FM-DB] Getting media name for title: {title}")
            return cls.get("search", params={"q": title}).json()["description"][0][
                "#TITLE"
            ]
        except Exception as e:
            logger.warning(
                f"Failed to fetch media name for title {title}: {e.__class__.__name__} | {e}"
            )
            return None

    @classmethod
    def get_media_by_title(cls, title: str):
        """
        Get limited media data by title,
        used as a fallback when the id is not found.
        Only returns the name and year fields.
        """
        try:
            logger.debug(f"[FM-DB] Trying to get media by title: {title}")
            data = cls.get("search", params={"q": title}).json()["description"][0]
            return {
                "name": data.get("#TITLE", title),
                "datePublished": f"{data.get('#YEAR', '0000')}-00-00",
            }
        except Exception as e:
            logger.warning(
                f"Failed to fetch data for title {title}: {e.__class__.__name__} | {e}"
            )
            return {}

    @classmethod
    def get_poster(cls, id: str, title: str | None = None, **kwargs):  # noqa: ARG003
        """
        Fetch the poster for a movie by its ID.

        Tries to fetch the poster using the fm-db api.
        If it fails, it will try to fetch the poster by title using another fm-db api endpoint, if the title is provided.
        If it fails, it will try to fetch the poster using the imdb.dev api.
        When all else fails, returns a default unknown poster image.
        """
        try:
            logger.debug(f"[FM-DB] Getting poster for movie with id: {id}")
            response = cls.get(f"/photo/{id}", params={"w": 300, "h": 440})
            return Image.open(io.BytesIO(response.content))
        except Exception as e:
            logger.warning(
                f"Failed to fetch poster with fm-db api for {id}: {e.__class__.__name__} | {e}"
            )
            if title:
                try:
                    return cls.get_poster_by_title(title)
                except Exception as e:
                    logger.warning(
                        f"Failed to fetch poster by title {title}: {e.__class__.__name__} | {e}"
                    )
            try:
                return ImdbdevClient.get_poster(id)
            except Exception as e:
                logger.warning(
                    f"Failed to fetch poster with imdb.dev api for {id}: {e.__class__.__name__} | {e}"
                )
                return UNKNOWN_POSTER

    @classmethod
    def get_poster_by_title(cls, title: str):
        """
        Get a poster for a movie by its title, used as a fallback when the id is not found.
        Fetches the image from imdb instead of the free movie database
        """
        logger.debug(f"[FM-DB] Trying to get poster by title: {title}")
        data = cls.get("search", params={"q": title}).json()["description"][0]
        poster_url = data.get("#IMG_POSTER", "")
        response = cls.session.get(poster_url)
        image = Image.open(io.BytesIO(response.content))
        image.thumbnail((300, 440))
        return image.convert("RGB")

    @classmethod
    def get_search_results(cls, title: str) -> list[dict[str, any]]:
        try:
            logger.debug(f"[FM-DB] Getting search results for title: {title}")
            response = cls.get("search", params={"q": title}).json()["description"]
            search_results = []
            for item in response:
                search_results.append(
                    {
                        "name": item.get("#TITLE", ""),
                        "year": item.get("#YEAR", ""),
                        "id": item.get("#IMDB_ID", ""),
                        "imdb_url": item.get("#IMDB_URL", ""),
                    }
                )
            return search_results
        except Exception as e:
            logger.warning(
                f"Failed to fetch search results for {title} with fm-db api: {e.__class__.__name__} | {e}"
            )
            return ImdbdevClient.get_search_results(title)
