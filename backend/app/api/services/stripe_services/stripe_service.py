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
# stripe.api_key = settings.stripe_secret_key

class StripeService(ServiceContext):
    def __init__(self, current_user, db):
        super().__init__(current_user, db)
    def create_customer(self, email: str, name: str):
        """Create stripe customer for tenants subscription billing"""
        logger.info('Creating stripe customer')
        customer = stripe.Customer.create(email=email, name=name)
        logger.info(f"Customer has been created {customer.id}")
        return customer.id
    def create_account_v2(self, email: str, full_name: str):
        """Create v2 stripe account this initializes an account and returns acct_id and customer_id for db records"""
        logger.debug(f'Creating v2 account ({email})')
        account = self.client.v2.core.accounts.create({
                                "contact_email": email,
                                "display_name": full_name,
                                "dashboard": "express",
                                "identity": {
                                    # "business_details": {"registered_name": company_name},
                                    "country": "US",
                                    "entity_type": "individual",
                                },
                                "configuration": {
                                        "merchant": {
                                            "capabilities": {
                                                "card_payments": {"requested": True}
                                                # "stripe_balance.payouts": {"requested": True}
                                            },
                                        },
                                        "customer":{
                                            "capabilities":{
                                                "automatic_indirect_tax": {"requested":True}
                                            }
                                        }
                                },
                                "defaults": {
                                    "currency": "usd", 
                                    "responsibilities": {
                                        "fees_collector": "stripe",
                                        "losses_collector": "stripe",
                                    },
                                    "locales":["en-US"],
                                },
                                
                                "include": [
                                        "configuration.customer",
                                        "configuration.merchant",
                                        "identity",
                                        "requirements"
                                    ],
                                
                                }
                            )
        account_id = account.id
        if account.configuration and account.configuration.customer:
            customer_id = account.configuration.customer.id  # Format: cus_123...
            logger.debug(f"Account ID: {account_id}, Customer ID: {customer_id}")
            return (account_id, customer_id)
        else:
            logger.debug(f"Account ID: {account_id}, No customer configuration found")
            logger.error(f"There should be a customer_if. Something is broken.")
            return account_id, None
    def update_account_type(self):
        """This handles account update form individual to rigistered business"""
        pass
    def add_account_metdata(self, tenant_id, acct_id):
        
        updated_account = self.client.v2.core.accounts.update(
            acct_id,
            {
                "metadata":{
                    "tenant_id": tenant_id
                }    
            }
        )
        
        return updated_account
    
    def create_express_account(self,tenant_obj: tenant_table, country: str = "US"):
        """Create Express account for tenant"""
        slug:str = tenant_obj.slug
        
        logger.debug("Creating account")
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
                            business_profile={
                                "name": slug.capitalize(), # The legal name of the business
                                # "url": f"https://{slug}.{self.DOMAIN}.com", # Helps Stripe verify the business
                                "mcc": "4121", # Merchant Category Code (4121 is for Taxicabs/Limousines/Livery)
                                "product_description": (
                                    f"Independent luxury transportation provider offering professional "
                                    f"chauffeur and black car services via the Maison platform. "
                                    f"Services include scheduled airport transfers, corporate travel, and "
                                    f"private event bookings, with payments processed upon booking completion."
                                ),
                            },
                            settings={
                                "branding": {
                                    "primary_color": "#6c63e8", # Your SaaS brand color
                                    "secondary_color": "#e7e6f0",
                                }
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
        response:tenant_profile = self.db.query(tenant_profile).filter(tenant_profile.tenant_id == tenant_obj.id).first()
        response.stripe_account_id = exp_acct_id
        self.db.add(response)
        self.db.commit()
        # onboarding_link = stripe.AccountLink.create(
        #     account=exp_acct_id,
        #     refresh_url=f"{self.BASE_URL}/tenant/reauth",
        #     return_url=f"{self.BASE_URL}/tenant/return",
        #     type="account_onboarding",
            
        # )
        
        return {"acct_id":exp_acct_id}
    def complete_account_setup(self):
        resp:tenant_table = self.db.query(tenant_table).filter(tenant_table.id == self.tenant_id).first()
        profile:tenant_profile = self.db.query(tenant_profile).filter(tenant_profile.tenant_id == self.tenant_id).first()
        acct_id = profile.stripe_account_id
        if resp and not resp.is_verified:
            onboarding_link = stripe.AccountLink.create(
                    account=acct_id,  # Your existing Account ID
                    refresh_url=f"{self.BASE_URL}/tenant/reauth",
                    return_url=f"{self.BASE_URL}/tenant/return",
                    type="account_onboarding",
                    collection_options={
                        "fields": "eventually_due", # Use "eventually_due" to get them fully set up
                    }
                    )
            return {'onboarding_link': onboarding_link.url}
        
        return None
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
    