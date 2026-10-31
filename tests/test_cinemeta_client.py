from PIL import Image

from services.cinemeta_client import CinemetaClient

MOVIE_TITLE = "Interstellar"
MOVIE_IMDB_ID = "tt0816692"
SHOW_TITLE = "Game of Thrones"
SHOW_IMDB_ID = "tt0944947"


def test_search_media_returns_tt_id():
    media_id = CinemetaClient.search_media(MOVIE_TITLE, media_type="movie")
    assert media_id == MOVIE_IMDB_ID


def test_get_media_movie():
    data = CinemetaClient.get_media(MOVIE_IMDB_ID, media_type="movie")
    assert data["name"] == MOVIE_TITLE
    assert data["aggregateRating"]["ratingValue"] > 0
    assert data["duration"] == 169
    assert data["datePublished"] == "2014-11-07"


def test_get_media_series():
    data = CinemetaClient.get_media(SHOW_IMDB_ID, media_type="series")
    assert data["name"] == SHOW_TITLE
    assert data["aggregateRating"]["ratingValue"] > 0


def test_get_show_counts():
    episodes, seasons = CinemetaClient.get_show_counts(SHOW_IMDB_ID)
    assert episodes == 73
    assert seasons == 8


def test_get_poster_returns_image():
    poster = CinemetaClient.get_poster(MOVIE_IMDB_ID, media_type="movie")
    assert isinstance(poster, Image.Image)
    assert poster.mode == "RGB"


def test_get_search_results():
    results = CinemetaClient.get_search_results(MOVIE_TITLE, media_type="movie")
    assert results, "expected at least one search result"
    assert all(r.id and str(r.id).startswith("tt") for r in results)
    assert results[0].id == MOVIE_IMDB_ID


def test_get_search_results_series():
    results = CinemetaClient.get_search_results(SHOW_TITLE, media_type="series")
    assert results, "expected at least one search result"
    assert results[0].id == SHOW_IMDB_ID
