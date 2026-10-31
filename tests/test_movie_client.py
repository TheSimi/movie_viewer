from PIL import Image

from media_classes.movie import Movie
from services.movie_client import MovieClient

TITLE = "Inception"
IMDB_ID = "tt1375666"


def test_search_media():
    media_id = MovieClient.search_media(TITLE)
    assert media_id == IMDB_ID


def test_get_media_returns_validated_movie():
    movie = MovieClient.get_media(IMDB_ID, title=TITLE, path="")
    assert isinstance(movie, Movie)
    assert movie.name == TITLE
    assert movie.rating > 0
    assert movie.runtime == 148
    assert isinstance(movie.image, Image.Image)


def test_get_poster():
    poster = MovieClient.get_poster(IMDB_ID, title=TITLE)
    assert isinstance(poster, Image.Image)
    assert poster.mode == "RGB"


def test_get_search_results():
    results = MovieClient.get_search_results(TITLE)
    assert results, "expected at least one search result"
    assert all(r.id and str(r.id).startswith("tt") for r in results)
    assert results[0].id == IMDB_ID
