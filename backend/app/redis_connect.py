import redis
from app.config import Settings 
import logging

logger = logging.getLogger(__name__)

settings = Settings()
redis_client = redis.Redis(
    host= settings.host,
    port= settings.redis_port,
    db=0
)
try:
    redis_client.ping()
    print("^_^ Redis Connection successful")
    # logging.info("^_^Redis Connection successful")

except redis.ConnectionError:
    logging.info("❌ Redis connection failed - make sure Redis is running")
