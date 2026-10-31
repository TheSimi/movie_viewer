import time

from PIL import Image

from services.wikidata_client import WikidataClient

TITLE = "Memento"
IMDB_ID = "tt0209144"


def test_full_flow():
    results = WikidataClient.get_search_results(TITLE)
    assert results, "expected at least one search result"
    assert all(r.id and str(r.id).startswith("tt") for r in results)
    media_id = str(results[0].id)
    assert media_id == IMDB_ID

    time.sleep(2)  # To deal with wikidata rate limit
    data = WikidataClient.get_media(media_id, TITLE)
    assert data["name"].lower() == "memento"
    assert data["datePublished"] == "2000-09-05"

    time.sleep(2)
    try:
        poster = WikidataClient.get_poster(media_id, TITLE)
    except ValueError:
        return  # wikidata does not always hold posters
    assert isinstance(poster, Image.Image)
    assert poster.mode == "RGB"
