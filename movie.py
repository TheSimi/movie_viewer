import os

class Movie:
    def __init__(self, path: str):
        self.path = path
        if os.path.isfile(path):
            self.is_file = True
            self.name = os.path.basename(path).split('.')[0]
        else:
            self.is_file = False
            self.name = os.path.basename(path)[1:]