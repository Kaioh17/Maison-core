import stripe
from stripe import StripeClient
from app.config import Settings
from app.utils.logging import logger
settings = Settings()
sk = settings.stripe_secret_key
stripe.api_key = sk

class ServiceContext:
    def __init__(self, current_user, db):
        self.current_user = current_user
        self.db = db
        settings = Settings()
        stripe.api_key = settings.stripe_secret_key
        self.client = StripeClient(sk) # for stripe connect v2
        self.BASE_URL = settings.base_url
        # Tenant-operator dashboard lives on its own `app.` subdomain, not the
        # apex/marketing host -- every Stripe redirect back into /tenant/* must
        # land there. Computed once here so callers don't each re-derive it.
        if "://" in self.BASE_URL:
            _scheme, _host = self.BASE_URL.split("://", 1)
            self.TENANT_APP_BASE_URL = f"{_scheme}://app.{_host}"
        else:
            self.TENANT_APP_BASE_URL = f"app.{self.BASE_URL}"
        self.DOMAIN = settings.domain
        self.WEBHOOK_SECRET = settings.webhook_secret
        self.CONNECT_WEBHOOK_SECRET = settings.connect_webhook_secret
        self.BILLING_PORTAL_CONFIG_ID = settings.stripe_billing_portal_config_id
        if self.current_user:
            self.role = self.current_user.role
            if self.role == 'tenant':
                self.sub_plan = self.current_user.subscription_plan
                self.tenant_id = self.current_user.id
            else:
                self.sub_plan = self.current_user.tenants.subscription_plan
                self.tenant_id = self.current_user.tenant_id
            # self.customer_id = self.current_user.stripe_customer_id
            # self.tenant_id = self.current_user.id
            # self.current_sub_id = self.current_user.cur_subscription_id
            logger.debug(f"Running stripe {self.role}")