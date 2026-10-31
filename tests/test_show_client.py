from PIL import Image

from media_classes.show import Show
from services.show_client import ShowClient

TITLE = "Game of Thrones"
IMDB_ID = "tt0944947"
TVMAZE_ID = 82


def test_search_media():
    tvmaze_id, imdb_id = ShowClient.search_media(TITLE)
    assert imdb_id == IMDB_ID or tvmaze_id == TVMAZE_ID


def test_get_media_returns_validated_show():
    tvmaze_id, imdb_id = ShowClient.search_media(TITLE)
    show = ShowClient.get_media((tvmaze_id, imdb_id), title=TITLE, path="")
    assert isinstance(show, Show)
    assert show.name == TITLE
    assert show.rating > 0
    assert show.episodes == 73
    assert show.seasons == 8
    assert isinstance(show.image, Image.Image)


def test_get_media_by_imdb_id_only():
    show = ShowClient.get_media(IMDB_ID, title=TITLE, path="")
    assert isinstance(show, Show)
    assert show.name == TITLE


def test_get_poster():
    poster = ShowClient.get_poster((TVMAZE_ID, IMDB_ID))
    assert isinstance(poster, Image.Image)
    assert poster.mode == "RGB"


def test_get_search_results():
    results = ShowClient.get_search_results(TITLE)
    assert results, "expected at least one search result"
