import os
import shutil
import stat

from const import CACHE_DIR, CACHE_VERSION
from media_classes import Movie, Show

def cache_path(path: str) -> str:
    basename = os.path.basename(path)
    # sum the values of the characters in the path
    char_sum = 0
    for i in path:
        char_sum += ord(i)
    basename = basename + '_' + str(char_sum)
    return os.path.join(CACHE_DIR, basename)


def clear_all_cache():
    for filename in os.listdir(CACHE_DIR):
            file_path = os.path.join(CACHE_DIR, filename)
            os.chmod(file_path, stat.S_IWUSR)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')


def clean_cache(movie_list: list[Movie], show_list: list[Show]):
    movie_path_list = [movie.cache_path(movie.path) for movie in movie_list]
    show_path_list = [show.cache_path(show.path) for show in show_list]

    full_path_list = movie_path_list + show_path_list

    for basename in os.listdir(CACHE_DIR):
        full_path = os.path.join(CACHE_DIR, basename)
        if os.path.isdir(full_path) and full_path not in full_path_list:
            os.chmod(full_path, stat.S_IWUSR)
            try:
                shutil.rmtree(full_path)
            except Exception as e:
                print(f'Failed to delete {full_path}. Reason: {e}')

def make_cache_version_file():
    version_file = os.path.join(CACHE_DIR, "version.txt")
    with open(version_file, 'w') as f:
        f.write(CACHE_VERSION)
