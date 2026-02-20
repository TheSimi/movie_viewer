import re
from media_classes.media import Media
from services.show_client import ShowClient

class Show(Media):
    def __init__(self, path: str):
        super().__init__(path, ShowClient)
        
        self.name = self.data['name']
        self.plot = re.sub(r'<.*?>', '', self.data['summary'])
        self.rating = self.data['rating']['average']
        self.year = self.data['premiered'].split('-')[0]
        # TODO - get episodes and seasons numbers