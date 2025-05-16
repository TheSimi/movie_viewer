import os
import pickle
from media import Media

from const import CACHE_DIR

def cache_path(path: str):
    return os.path.join(CACHE_DIR, "+".join(path.split(os.sep)))

def get_file_list(folder_list: list, file_in_folder_func: callable, file_class: Media):
    file_path_list = []
    for folder in folder_list:
        file_path_list.extend(file_in_folder_func(folder))
    file_list = []
    for file in file_path_list:
        if os.path.exists(cache_path(file)):
            file_list.append(file_class.load_from_cache(cache_path(file)))
        else:
            instance = file_class(file)
            file_list.append(instance)
            instance.save_to_cache()
    return file_list

def get_from_cache(cache_file: str):
    with open(cache_file, 'rb') as f:
        f.seek(0)
        media = pickle.load(f)
    return media

def get_shows_in_folder(folder: str):
    show_list = []
    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)
        if os.path.isdir(file_path):
            if file.startswith('-'):
                show_list.extend(
                    get_shows_in_folder(file_path)
                )
            else:
                show_list.append(file_path)
    return show_list

def get_movies_in_folder(folder: str):
    movie_list = []
    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)
        if os.path.isfile(file_path):
            movie_list.append(file_path)
        elif os.path.isdir(file_path):
            if file.startswith('-'):
                movie_list.append(file_path)
            else:
                movie_list.extend(
                    get_movies_in_folder(file_path)
                )
    return movie_list
