import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s: [%(levelname)s] - %(message)s'
)

logger = logging.getLogger("movie_viewer_logger")
logger.setLevel(logging.DEBUG)