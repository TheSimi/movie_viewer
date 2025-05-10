import abc
import os
import subprocess
import shutil

from const import MEDIA_PLAYER

class Media(abc.ABC):
    def __init__(self):
        pass

    @abc.abstractmethod
    def play(self):
        pass

class Movie(Media):
    def __init__(self, path: str):
        self.path = path
        if os.path.isfile(path):
            self.is_file = True
            self.name = os.path.basename(path).split('.')[0]
        else:
            self.is_file = False
            self.name = os.path.basename(path)[1:]
    
    def play(self):
        if self.is_file:
            subprocess.Popen([MEDIA_PLAYER, self.path])
        else:
            first_file = os.path.join(self.path, os.listdir(self.path)[0])
            subprocess.Popen(f'explorer /select,"{first_file}"')

class Show(Media):
    def __init__(self, path: str):
        self.name = os.path.basename(path)
        self.path = path
        self.episode_list = self.get_episode_list()
    
    def get_episode_list(self):
        episode_list = []
        for file in os.listdir(self.path):
            if os.path.isfile(os.path.join(self.path, file)):
                episode_list.append(file)
        return episode_list
    
    def play(self):
        if not os.path.exists(os.path.join(self.path, "watched")):
            os.makedirs(os.path.join(self.path, "watched"))
        
        if self.episode_list:
            current_episode = self.episode_list.pop(0)
            shutil.move(
                os.path.join(self.path, current_episode),
                os.path.join(self.path, "watched", current_episode)
            )
            current_episode = os.path.join(self.path, "watched", current_episode)
            subprocess.Popen([MEDIA_PLAYER, current_episode])
