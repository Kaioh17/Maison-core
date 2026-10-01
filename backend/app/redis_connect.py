import redis
from app.config import Settings 
import logging

logger = logging.getLogger(__name__)

settings = Settings()
# from_url so a password in redis_url (redis://:password@host:6379) is honoured, same as Celery.
redis_client = redis.Redis.from_url(settings.redis_url, db=0)
try:
    redis_client.ping()
    print("^_^ Redis Connection successful")
    # logging.info("^_^Redis Connection successful")

except redis.ConnectionError:
    logging.info("❌ Redis connection failed - make sure Redis is running")
