###logging settings
import time
import logging
import sys
import os
# Ensure the logs directory exists
os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("maison_logger")
logger.setLevel(logging.DEBUG)


#stream handler
if not logger.hasHandlers():
    stream_handler = logging.StreamHandler(sys.stdout)
    
    log_formatter = logging.Formatter("%(asctime)s  [%(levelname)s] - %(message)s ")
    stream_handler.setFormatter(log_formatter)
    logger.addHandler(stream_handler)
    
    
    file_handler = logging.FileHandler("logs/maison.log")
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

logger.propagate = False
# logger.info("starting fast api")