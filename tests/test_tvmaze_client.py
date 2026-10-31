from PIL import Image

from services.tvmaze_client import TvmazeClient

TITLE = "breaking bad"
TV_MAZE_ID = 169
IMDB_ID = "tt0903747"


def test_search_media_returns_ids():
    tvmaze_id, imdb_id = TvmazeClient.search_media(TITLE)
    assert tvmaze_id == TV_MAZE_ID
    assert imdb_id == IMDB_ID


def test_get_media_flow():
    data = TvmazeClient.get_media(TV_MAZE_ID)
    assert data["name"].lower() == TITLE


def test_get_poster_returns_image():
    poster = TvmazeClient.get_poster(TV_MAZE_ID)
    assert isinstance(poster, Image.Image)
    assert poster.mode == "RGB"


def test_get_search_results():
    results = TvmazeClient.get_search_results(TITLE)
    assert results, "expected at least one search result"
    assert any(r.name.lower() == TITLE for r in results)
