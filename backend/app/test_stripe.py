import stripe
from config import Settings
from utils.logging import logger
from dotenv import load_dotenv
load_dotenv()

settings = Settings()
stripe.api_key = settings.sk_test

logger.info(f"Stripe Account: {stripe.Account.retrieve()}")
