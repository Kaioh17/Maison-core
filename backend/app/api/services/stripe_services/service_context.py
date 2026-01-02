import stripe
from app.config import Settings
from app.utils.logging import logger
settings = Settings()
stripe.api_key = settings.sk_test

class ServiceContext:
    def __init__(self, current_user, db):
        self.current_user = current_user
        self.db = db
        settings = Settings()
        stripe.api_key = settings.sk_test
        self.BASE_URL = settings.base_url
        self.WEBHOOK_SECRET = settings.webhook_secret
        self.CONNECT_WEBHOOK_SECRET = settings.connect_webhook_secret
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