import os

import dotenv
from PIL import Image, ImageDraw, ImageFont

dotenv.load_dotenv(override=True)

RETRY_AMOUNT = 5

MOVIE_FOLDERS = (
    os.getenv("MOVIE_FOLDERS").split(",") if os.getenv("MOVIE_FOLDERS") else []
)
SHOW_FOLDERS = os.getenv("SHOW_FOLDERS").split(",") if os.getenv("SHOW_FOLDERS") else []
try:
    PLAY_SPEED = float(os.getenv("SPEED")) if os.getenv("SPEED") else 1.0  # type: ignore
except ValueError:
    PLAY_SPEED = 1.0

CACHE_DIR = os.path.join(os.getenv("LOCALAPPDATA"), "movie_viewer", ".cache")  # type: ignore
CACHE_VERSION = "0.2.2"

MEDIA_PLAYER = os.getenv("MEDIA_PLAYER") if os.getenv("MEDIA_PLAYER") else "vlc"
if MEDIA_PLAYER.lower() == "vlc":
    MEDIA_PLAYER = r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
elif MEDIA_PLAYER.lower() == "wmplayer":
    MEDIA_PLAYER = r"C:\Program Files (x86)\Windows Media Player\wmplayer.exe"

VIDEO_EXTENTIONS = (
    ".avi",
    ".mov",
    ".mp4",
    ".wmv",
    ".flv",
    ".mkv",
    ".webm",
    ".mpg",
    ".mpeg",
    ".avchd",
    ".mts",
    ".3pg",
    ".ogv",
)
SUBTITLE_EXTENTIONS = (
    ".sub",
    ".srt",
    ".ssa",
    ".ass",
    ".jss",
    ".SAMI",
    ".txt",
    ".idx",
    ".usf",
    ".ogm",
    ".ogg",
)

UNKNOWN_POSTER = Image.new("RGB", (300, 440), color="black")
_unknown_poster_draw = ImageDraw.Draw(UNKNOWN_POSTER)
_unknown_poster_font = ImageFont.load_default(size=128)
_unknown_poster_text_bbox = _unknown_poster_draw.textbbox(
    (0, 0), "?", font=_unknown_poster_font
)
_unknown_poster_text_width = _unknown_poster_text_bbox[2] - _unknown_poster_text_bbox[0]
_unknown_poster_text_height = (
    _unknown_poster_text_bbox[3] - _unknown_poster_text_bbox[1]
)
_unknown_poster_x = (300 - _unknown_poster_text_width) / 2
_unknown_poster_y = (440 - _unknown_poster_text_height) / 2
if "text_bbox" in locals():
    _unknown_poster_x -= _unknown_poster_text_bbox[0]
    _unknown_poster_y -= _unknown_poster_text_bbox[1]
_unknown_poster_draw.text(
    (_unknown_poster_x, _unknown_poster_y), "?", fill="white", font=_unknown_poster_font
)

IDLE_BUTTON_STYLESHEET = (
    "border: 2px solid #222; background-color: none; border-radius: 4px; color: white;"
)
FOCUSED_BUTTON_STYLESHEET = (
    "border: 2px solid white; background-color: none; border-radius: 4px; color: white;"
)
TEXT_LABEL_STYLESHEET = "color: white; background: none; border: none;"
IMAGE_LABEL_STYLESHEET = "background: none; border: none;"
