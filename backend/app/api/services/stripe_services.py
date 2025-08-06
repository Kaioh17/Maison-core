import stripe
from app.config import Settings
from app.utils.logging import logger
settings = Settings()
stripe.api_key = settings.sk_test

class StripeService:
    
    def create_customer(email: str, name: str):
        """Create stripe customer for tenants subscription billing"""
        
        customer = stripe.Customer.create(email=email)
        logger.info(f"Customer has been created {customer.id}")
        return customer.id

    def create_express_account(email: str, country: str = "US"):
        """Create Express account for tenant"""

        express_account = stripe.Account.create(type="express", country=country,
                                        email=email, 
                                        capabilities={
                                            "transfers": {"requested":True},
                                            "card_payments": {"requested":True}
                                        }
                                        )
        logger.info(f"Express account has been created [{express_account.id}] for {email}")
        
        
        return express_account.id