import stripe
from app.config import Settings
from app.utils.logging import logger
from .service_context import ServiceContext
# settings = Settings()
# stripe.api_key = settings.sk_test

class StripeService(ServiceContext):
  
    def create_customer(email: str, name: str):
        """Create stripe customer for tenants subscription billing"""
        
        customer = stripe.Customer.create(email=email, name=name)
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
    
    def create_onboarding_link(express_account_id):
        
        account_link = stripe.AccountLink.create(
            account=express_account_id,
            refresh_url = "https://retry-onboarding", #where they when they fail
            return_url = "https://onboarding-complete", # where they go onoce it passes 
            type="account_onboarding"
        )

        return account_link.id