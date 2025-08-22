import dotenv
import os

dotenv.load_dotenv(override=True)

MOVIE_FOLDERS = os.getenv('MOVIE_FOLDERS').split(',') if os.getenv('MOVIE_FOLDERS') else []
SHOW_FOLDERS = os.getenv('SHOW_FOLDERS').split(',') if os.getenv('SHOW_FOLDERS') else []
try:
    PLAY_SPEED = float(os.getenv('SPEED')) if os.getenv('SPEED') else 1.0
except ValueError:
    PLAY_SPEED = 1.0

CACHE_DIR = os.path.join(os.getenv('LOCALAPPDATA'), "movie_viewer", ".cache")
CACHE_VERSION = "0.2.1"

MEDIA_PLAYER = os.getenv('MEDIA_PLAYER') if os.getenv('MEDIA_PLAYER') else "vlc"
if MEDIA_PLAYER.lower() == 'vlc':
    MEDIA_PLAYER = r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
elif MEDIA_PLAYER.lower() == 'wmplayer':
    MEDIA_PLAYER = r"C:\Program Files (x86)\Windows Media Player\wmplayer.exe"

VIDEO_EXTENTIONS = (
    ".avi", ".mov", ".mp4", ".wmv", ".flv", ".mkv", ".webm",
    ".mpg", ".mpeg", ".avchd", ".mts", ".3pg", ".ogv"
)
SUBTITLE_EXTENTIONS = (
    ".sub", ".srt", ".ssa", ".ass", ".jss", ".SAMI", ".txt",
    ".idx", ".usf",  ".ogm", ".ogg"
)