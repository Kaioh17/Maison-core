import stripe
from app.config import Settings

settings = Settings()
stripe.api_key = settings.sk_test

class StripeService:
    
    def create_subscription(customer_id, price_id):
        pass

    
    def get_customer_subscription_status(customer_id):
        pass

    def upgrade_subscriptio(subscription_id, new_price_id):
        pass