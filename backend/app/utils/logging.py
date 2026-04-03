###logging settings
# import time
# import logging
# import sys
# import os

# # Ensure the logs directory exists
# os.makedirs("logs", exist_ok=True)

# logger = logging.getLogger("maison_logger")
# logger.setLevel(logging.DEBUG)


# #stream handler
# if not logger.hasHandlers():
#     stream_handler = logging.StreamHandler(sys.stdout)
    
#     log_formatter = logging.Formatter("%(asctime)s  [%(levelname)s] - %(message)s ")
#     stream_handler.setFormatter(log_formatter)
#     logger.addHandler(stream_handler)
    
    
#     file_handler = logging.FileHandler("logs/maison.log")
#     file_handler.setFormatter(log_formatter)
#     logger.addHandler(file_handler)

# logger.propagate = False
# # logger.info("starting fast api")

"""
Logging configuration for Papelly backend.
Supports both development and production environments.
"""
import time
import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# backend/ — load .env before Settings() so os.environ matches file for any non-Settings readers
backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(backend_dir / "app" / ".env")

from app.config import Settings

settings = Settings()

# Determine environment (defaults to development)
environment = settings.environment
environment = environment.lower()
# environment = "production"

# Create logs directory in the backend folder (relative to this file)
# This ensures logs are created in backend/logs/ regardless of where the app runs from
logs_dir = backend_dir / "logs"
logs_dir.mkdir(exist_ok=True)

# Create logger
logger = logging.getLogger("maison_logger")

# Set log level based on environment
if environment == "production":
    logger.setLevel(logging.INFO)  # INFO level for production
else:
    logger.setLevel(logging.DEBUG)  # DEBUG level for development

class CustomFormatter(logging.Formatter):
    """Custom formatter that includes environment information."""
    def format(self, record):
        record.environment = environment[:4]
        return super().format(record)

# Configure formatter with environment info
log_formatter = CustomFormatter(
    "%(asctime)s [%(environment)s] %(name)s [%(levelname)s] - %(message)s"
)
logging.Formatter.converter = time.gmtime  # Use UTC time

# Configure handlers only if logger doesn't have them (prevents duplicate logs)
if not logger.hasHandlers():
    # Stream handler - always logs to stdout (for Render logs)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(log_formatter)
    stream_handler.setLevel(logging.DEBUG if environment == "development" else logging.INFO)
    logger.addHandler(stream_handler)
    
    # File handler - logs to file based on environment
    if environment == "production":
        log_file = logs_dir / "maison_production.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)  # Only INFO and above in production
    else:
        log_file = logs_dir / "maison_dev.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # All levels in development
    
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

# Prevent propagation to root logger
logger.propagate = False