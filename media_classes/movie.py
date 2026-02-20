from media_classes.media import Media
from services.movie_client import MovieClient

class Movie(Media):
    def __init__(self, path: str):
        super().__init__(path, MovieClient)
        
        self.name = self.data['name']
        self.plot = self.data['description']
        self.rating = self.data['aggregateRating']['ratingValue']
        self.runtime = self.data['duration']
        self.year = int(self.data['datePublished'].split('-')[0])