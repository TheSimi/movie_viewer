import dotenv
import os

dotenv.load_dotenv(override=True)

MOVIE_FOLDERS = os.getenv('MOVIE_FOLDERS').split(',') if os.getenv('MOVIE_FOLDERS') else []
SHOW_FOLDERS = os.getenv('SHOW_FOLDERS').split(',') if os.getenv('SHOW_FOLDERS') else []

CACHE_DIR = ""
if os.name == 'nt': 
    CACHE_DIR = f"{os.getenv('LOCALAPPDATA')}\\movie_viewer\\.cache"
elif os.name == 'posix':
    CACHE_DIR = os.path.expanduser('~/.local/share/movie_viewer/.cache')
CACHE_VERSION = "0.2.0"

MEDIA_PLAYER = os.getenv('MEDIA_PLAYER') if os.getenv('MEDIA_PLAYER') else ""
if MEDIA_PLAYER.lower() == 'vlc' or MEDIA_PLAYER == "":
    MEDIA_PLAYER = r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
elif MEDIA_PLAYER.lower() == 'wmplayer':
    MEDIA_PLAYER = r"C:\Program Files (x86)\Windows Media Player\wmplayer.exe"