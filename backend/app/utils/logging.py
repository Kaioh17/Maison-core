###logging settings
import logging
import sys

logger = logging.getLogger("maison_loger")
logger.setLevel(logging.DEBUG)


#stream handler
if not logger.hasHandlers():
    stream_handler = logging.StreamHandler(sys.stdout)
    log_formatter = logging.Formatter("%(asctime)s  [%(levelname)s] - %(message)s ")
    stream_handler.setFormatter(log_formatter)
    logger.addHandler(stream_handler)
    
logger.propagate = False
# logger.info("starting fast api")