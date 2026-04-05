import os
import shutil
import stat

from const import CACHE_DIR, CACHE_VERSION


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


def clean_cache(media_list: dict[type, list]):
    full_path_list = []
    for media_items in media_list.values():
        for media in media_items:
            full_path_list.append(media.cache_path(media.path))

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

def check_cache() -> bool:
    if not os.path.exists(CACHE_DIR):
        return False
    version_file = os.path.join(CACHE_DIR, "version.txt")
    if not os.path.exists(version_file):
        return False
    with open(version_file) as f:
        version = f.read().strip()
    return version == CACHE_VERSION

def cache_version_handler() -> None:
    """
    Checks if the cache is valid by checking the cache version file.
    """
    if not check_cache():
        os.makedirs(CACHE_DIR, exist_ok=True)
        clear_all_cache()

        # Update cache version
        make_cache_version_file()
