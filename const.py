import dotenv
import os

dotenv.load_dotenv()

MOVIE_FOLDERS = os.getenv('MOVIE_FOLDERS').split(',')
SHOW_FOLDERS = os.getenv('SHOW_FOLDERS').split(',')

CACHE_DIR = os.path.join(os.getenv('CACHE_DIR'), ".cache")
if CACHE_DIR is None:
    CACHE_DIR = os.path.join(os.path.curdir, ".cache")

MEDIA_PLAYER = os.getenv('MEDIA_PLAYER')
if MEDIA_PLAYER.lower() == 'vlc':
    MEDIA_PLAYER = r"C:/Program Files (x86)/VideoLAN/VLC/vlc.exe"
elif MEDIA_PLAYER is None or MEDIA_PLAYER.lower() == 'wmplayer':
    MEDIA_PLAYER = r"C:/Program Files (x86)/Windows Media Player/wmplayer.exe"