import logging

import colorlog

colors = {
    'DEBUG':    'cyan',
    'INFO':     'green',
    'WARNING':  'yellow',
    'ERROR':    'red',
    'CRITICAL': 'red,bg_white',
}

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    fmt='%(log_color)s%(asctime)s: [%(levelname)s] - %(message)s',
    log_colors=colors
))

logger = logging.getLogger("movie_viewer_logger")
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
logger.propagate = False