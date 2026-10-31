from PIL import Image

from services.imdb_client import IMDbClient

MOVIE_TITLE = "Inception"
MOVIE_IMDB_ID = "tt1375666"
SHOW_TITLE = "Game of Thrones"
SHOW_IMDB_ID = "tt0944947"


def test_search_media_returns_id_string():
    media_id = IMDbClient.search_media(MOVIE_TITLE)
    assert media_id == MOVIE_IMDB_ID


def test_get_media_has_imdb_data():
    data = IMDbClient.get_media(MOVIE_IMDB_ID)
    print(data)
    assert data["name"] == "Inception"
    assert data["aggregateRating"]["ratingValue"] > 0
    assert data["duration"] == 148
    assert data["datePublished"] == "2010-07-16"
    assert data["description"]


def test_get_poster_returns_image():
    poster = IMDbClient.get_poster(MOVIE_IMDB_ID)
    assert isinstance(poster, Image.Image)
    assert poster.mode == "RGB"
    assert poster.size[0] <= 300 and poster.size[1] <= 440


def test_format_for_movie():
    formatted = IMDbClient.format_for_movie(IMDbClient.get_media(MOVIE_IMDB_ID))
    assert formatted["name"] == "Inception"
    assert formatted["aggregateRating"]["ratingValue"] > 0
    assert formatted["duration"] == 148


def test_format_for_show():
    formatted = IMDbClient.format_for_show(IMDbClient.get_media(SHOW_IMDB_ID))
    assert formatted["name"] == SHOW_TITLE
    assert formatted["rating"]["average"] > 0


def test_search_returns_known_id():
    results = IMDbClient.get_search_results(MOVIE_TITLE)
    assert results, "expected at least one search result"
    assert all(r.id and str(r.id).startswith("tt") for r in results)
    assert results[0].id == MOVIE_IMDB_ID
