###logging settings
import logging
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


#stream handler
stream_handler = logging.StreamHandler(sys.stdout)
log_formatter = logging.Formatter("%(asctime)s  [%(levelname)s] - %(message)s ")
stream_handler.setFormatter(log_formatter)

logger.propagate = False

logger.addHandler(stream_handler)

logger.info("starting fast api")