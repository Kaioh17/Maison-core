import stripe
from app.config import Settings
from app.utils.logging import logger
from .service_context import ServiceContext
from ..helper_service import *
from ...core import deps

from app.config import Settings
from .service_context import ServiceContext
from fastapi import HTTPException, status, Depends
from app.db.database import get_db, get_base_db
# settings = Settings()
# stripe.api_key = settings.sk_test

class StripeService(ServiceContext):
    def __init__(self, current_user, db):
        super().__init__(current_user, db)
    def create_customer(email: str, name: str):
        """Create stripe customer for tenants subscription billing"""
        
        customer = stripe.Customer.create(email=email, name=name)
        logger.info(f"Customer has been created {customer.id}")
        return customer.id

    def create_express_account(self,tenant_obj: tenant_table, country: str = "US"):
        """Create Express account for tenant"""
        slug = tenant_obj.slug
        express_account = stripe.Account.create(
                            type="express", 
                            country=country,
                            email=tenant_obj.email,
                            business_type="individual",
                            individual={
                                "first_name": tenant_obj.first_name,
                                "last_name": tenant_obj.last_name,
                                "email": tenant_obj.email,
                                },
                           
                            capabilities={
                                "transfers": {"requested":True},
                                "card_payments": {"requested":True}
                            },
                            metadata={
                                "tenant_id":tenant_obj.id
                            }
                            )
        exp_acct_id = express_account.id
        logger.info(f"Express account has been created [{exp_acct_id}] for")
        
        onboarding_link = stripe.AccountLink.create(
            account=exp_acct_id,
            refresh_url=f"http://{self.BASE_URL}/tenant/reauth",
            return_url=f"http://{self.BASE_URL}/tenant/return",
            type="account_onboarding"
        )
        
        return {"acct_id":exp_acct_id, 'onboarding_link': onboarding_link.url}
    def get_account_link(self):
        stripe_account_id = self.current_user.profile.stripe_account_id
        logger.debug(f"sacct {stripe_account_id}")
        login_link = stripe.Account.create_login_link(stripe_account_id)
        
        return success_resp(data= {"login_link":login_link.url})
    def create_onboarding_link(express_account_id):
        
        account_link = stripe.AccountLink.create(
            account=express_account_id,
            refresh_url = "https://retry-onboarding", #where they when they fail
            return_url = "https://onboarding-complete", # where they go onoce it passes 
            type="account_onboarding"
        )

        return account_link.id
def get_stripe_service(current_user = Depends(deps.get_current_user), db = Depends(get_db)):
    return StripeService(current_user=current_user, db=db)
    