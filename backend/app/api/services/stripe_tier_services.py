import stripe
from app.config import Settings

settings = Settings()
stripe.api_key = settings.sk_test

class StripeService:
    
    """customer gets created (backend)
        (frontend) create payment_method_id after getting card details"""
    async def create_subscription(customer_id: str, price_id: str):
         
        return stripe.Subscription.create(
            customer=customer_id,
            items = [{"price": price_id}],
             default_payment_method=payment_method_id
        )


    
    async def get_customer_subscription_status(customer_id):
        subs = stripe.Subscription.list(customer=customer_id, limit =1)
        if subs.data:
            return subs.data[0].status 
        return None
    
    def upgrade_subscription(subscription_id, new_price_id):
        """Upgrade or downgrade plans"""
        subscription = stripe.Subscription.retrieeve(subscription_id)
        return stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=False,
            proration_behavior="create_prorations",
            items=[{
                "id": subscription["items"]["data"][0].id,
                "price": new_price_id
            }]
        )