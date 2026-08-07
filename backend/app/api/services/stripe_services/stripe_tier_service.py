import stripe
from app.config import Settings
from .service_context import ServiceContext
from fastapi import HTTPException, status, Depends
from app.db.database import get_db, get_base_db
from ...core import deps
from app.models import user, driver, tenant
from app.utils import password_utils, db_error_handler
from app.utils.logging import logger
from app.domain.billing import price_to_plan
from ..helper_service import tenant_setting_table, tenant_table, tenant_stats, tenant_profile, Validations, success_resp, failed_resp
# from .helper_service import Validations


class StripeService(ServiceContext):
    def __init__(self,current_user, db):
        super().__init__(current_user, db)
   
   
    # async def create_subscription(self,customer_id: str, price_id: str):
         
    #     return stripe.Subscription.create(
    #         customer=customer_id,
    #         items = [{"price": price_id}],
        
    #     )

    def _resolve_requested_plan(self, price_id, product_type):
        """Derive the plan from the Stripe price, never from the client.

        `product_type` is client-supplied; accepting it would let a tenant buy
        the growth price and receive fleet quotas. We resolve the price
        server-side and reject any request whose stated plan disagrees.
        """
        resolved = price_to_plan(price_id)
        if resolved is None:
            logger.warning(f"Rejected checkout for unknown price_id {price_id}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Unknown price_id")
        if product_type and product_type.strip().lower() != resolved:
            logger.warning(
                f"Tenant {self.current_user.id} requested plan '{product_type}' "
                f"with price_id {price_id} which maps to '{resolved}'. Rejected."
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="price_id does not match the requested plan")
        return resolved

    async def create_checkout_session(self, price_id, product_type):
        resolved_plan = self._resolve_requested_plan(price_id, product_type)
        try:
            logger.info(f"{self.current_user.slug} get customer")
            get_customer = self.db.query(tenant_profile).filter(tenant_profile.tenant_id == self.current_user.id).first()
            # valid = Validations._tenants_exist(get_customer)
            customer_id = get_customer.stripe_customer_id
            account_id = get_customer.stripe_account_id
            logger.info(f" creating checkout session {customer_id} {account_id}")
            logger.info(f"creating price_id {price_id}")
            sub_metadata = {
                'tenant_id': self.current_user.id,
                'product_type': resolved_plan
            }
            checkout_session = stripe.checkout.Session.create(
                line_items=[{
                    'price': price_id,
                    'quantity':1
                }],
                mode='subscription',
                # Founding-operator discount is a promotion code entered here,
                # not a discounted price id: a private commercial term must not
                # leak into the public catalogue /subscription/limits returns.
                allow_promotion_codes=True,
                # Explicit because a deep discount can drop the first invoice to
                # $0, and Stripe skips card collection when nothing is due. A
                # design partner with no card on file is a free pilot, which
                # PRICING_RATIONALE.md section 3 rules out.
                payment_method_collection='always',
                success_url= f"{self.BASE_URL}/success",
                cancel_url= f"{self.BASE_URL}/cancel",
                metadata=sub_metadata,
                subscription_data={'metadata': sub_metadata},
                customer=customer_id
            )
            logger.debug(f"Check out session completed")
            
            return success_resp(msg = "Successfully created checkout session", 
                                data = {'Checkout_session_url':checkout_session.url,
                                        'tenant_id': self.current_user.id,
                                        'customer_id': checkout_session.customer,
                                        'product_type': resolved_plan,
                                        'sub_total': checkout_session.amount_subtotal},
                                )
        except HTTPException:
            raise
        except Exception as e:
            # Previously swallowed and returned None, which then failed
            # response-model validation with an opaque error.
            logger.error(f"Checkout session creation failed: {e}")
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                                detail="Could not create checkout session")

    async def upgrade_subscription(self,price_id, product_type):
        """Start a tier change -- confirmed in Stripe's Billing Portal, not silently billed here.

        A price change on an existing subscription is real money movement
        (immediate prorated invoice via always_invoice). Calling
        `Subscription.modify()` directly from the API bills the tenant with
        zero on-screen confirmation of the card or the amount, which is
        exactly the auto-renewal-statute exposure flagged in
        directives.md security-isolation-2026-07. Instead we hand back a
        Billing Portal URL, scoped by `flow_data.subscription_update_confirm`
        to this one price change, so Stripe's own hosted screen shows the
        card on file and the prorated amount before anything bills. The
        actual `Subscription.modify` happens inside Stripe once the tenant
        confirms there; `customer.subscription.updated` (webhooks.py) picks
        up the resulting plan/status change same as any other Stripe-side
        update. See directives.md billing-confirm-2026-08.
        """
        resolved_plan = self._resolve_requested_plan(price_id, product_type)
        try:
            logger.info(f"{self.current_user.slug} get customer")
            get_customer = self.db.query(tenant_profile).filter(tenant_profile.tenant_id == self.current_user.id).first()
            # valid = Validations._tenants_exist(get_customer)
            customer_id = get_customer.stripe_customer_id
            current_sub_id = get_customer.cur_subscription_id
            if not current_sub_id:
                # Free-tier tenants hold no Stripe subscription (see billing.py) --
                # there is nothing to update, so their first paid plan is a new
                # Checkout session, not a portal-confirmed change.
                logger.info(f"{self.current_user.slug} has no subscription yet; starting checkout instead of upgrade")
                return await self.create_checkout_session(price_id, product_type)
            logger.info(f" creating billing portal session for {customer_id} ")
            subscription = stripe.Subscription.retrieve(current_sub_id)
            sub_item_id = subscription['items']['data'][0].id
            current_price_id = subscription['items']['data'][0]['price']['id']

            # The founding-operator coupon (see directives.md founding-terms-2026-08)
            # is scoped to the tier picked at signup and must not ride along onto a
            # higher-priced tier. Two things had to be true to strip it and neither
            # was, which is how a Fleet upgrade billed $0.00 in test-mode verification
            # (directives.md billing-confirm-2026-08):
            #   1. `Subscription.modify(discounts=[])` does NOT clear a discount --
            #      Stripe's own docs: an empty *array* "leaves discounts unchanged";
            #      only an empty *string* clears them.
            #   2. The Billing Portal's `subscription_update_confirm.discounts` field
            #      has no clear/remove semantics at all -- it only *applies* a coupon,
            #      so passing it anything was never going to strip the existing one.
            # So the discount has to be detached from the subscription itself, here,
            # server-side, with the one call Stripe documents as actually clearing it
            # -- before the portal session (which can only carry the state forward,
            # not fix it) is ever created.
            if price_id != current_price_id and (subscription.get('discount') or subscription.get('discounts')):
                stripe.Subscription.modify(current_sub_id, discounts="")

            portal_session = stripe.billing_portal.Session.create(
                customer=customer_id,
                configuration=self.BILLING_PORTAL_CONFIG_ID,
                return_url=f"{self.BASE_URL}/tenant/settings/plans",
                flow_data={
                    "type": "subscription_update_confirm",
                    "subscription_update_confirm": {
                        "subscription": current_sub_id,
                        "items": [{
                            "id": sub_item_id,
                            "price": price_id,
                            "quantity": 1,
                        }],
                    },
                    "after_completion": {
                        "type": "redirect",
                        "redirect": {"return_url": f"{self.BASE_URL}/tenant/settings/plans"},
                    },
                },
            )
            return success_resp(
                msg="Confirm your plan change",
                data={
                    'portal_url': portal_session.url,
                    'tenant_id': self.current_user.id,
                    'customer_id': customer_id,
                    'product_type': resolved_plan,
                },
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Billing portal session creation failed: {e}")
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                                detail="Could not start plan change")
    
    async def get_customer_subscription_status(customer_id):
        subs = stripe.Subscription.list(customer=customer_id, limit =1)
        if subs.data:
            return subs.data[0].status 
        return None
    

    
    
    # async def webhook(self,request):
    #     try:
    #         payload = await request.body()
    #         webhook_secret = self.WEBHOOK_SECRET
    #         sig_header = request.headers.get("stripe-signature")
    #         # logger.info()
    #         event = stripe.Webhook.construct_event(
    #             payload,
    #             sig_header,
    #             webhook_secret
    #         )
    #     except Exception as e:
    #         return 
    #     logger.debug(f"webhook event")
    #     if event['type'] == 'checkout.session.completed' :
    #         ##Update status in db version
    #         session  =event['data']['object']
            
    #         tenant_id = session.get('metadata', {}).get('tenant_id')
    #         stripe_customer_id = session.get('customer')
    #         plan = session.get('metadata',{}).get('product_type')
    #         subscription_id = session.get('subscription')
    #         logger.debug(f"Tenant {tenant_id} successfully subscribed. customer_id [{stripe_customer_id}] paln [{plan}] sub_id [{subscription_id}]")
    #         tenant_obj:tenant_profile = self.db.query(tenant_profile).filter(tenant_profile.tenant_id == tenant_id).first()
    #         tenant_obj.subscription_status = 'active'
    #         tenant_obj.subscription_plan = plan
    #         tenant_obj.cur_subscription_id = subscription_id
            
    #     elif event['type'] == 'customer.subscription.updated':
    #         # session  =event['data']['object']
    #         subscription = event['data']['object']
    
            
    #         subscription_id = subscription.get('id')
            
    #         stripe_customer_id = subscription.get('customer')
            
    #         metadata = subscription.get('metadata', {})
    #         tenant_id = metadata.get('tenant_id')
    #         plan = metadata.get('product_type')
    #         logger.debug(f"Tenant {tenant_id} successfully subscribed. customer_id [{stripe_customer_id}] paln [{plan}] sub_id [{subscription_id}]")
    #         tenant_obj:tenant_profile = self.db.query(tenant_profile).filter(tenant_profile.tenant_id == tenant_id).first()
    #         tenant_obj.subscription_status = 'active'
    #         tenant_obj.subscription_plan = plan
    #         tenant_obj.cur_subscription_id = subscription_id
    #     elif event['type'] == 'invoice.paid':
    #         # this triggers on every renewal
    #         invoice = event['data']['object']
    #         subscription_id = invoice.get('subscription')
    #         logger.debug(f"Payment successfull for sub: {subscription_id}")
            
    #         # logger.debug(f"{invoice}")
    #         ##send email notifying
    #     elif event['type'] == 'customer.subscription.deleted':
    #         subscription = event['data']['object']
    #         logger.debug(f"Subsripiton {subscription['id']} has ended.")
    #         tenant_obj:tenant_profile = self.db.query(tenant_profile).filter(tenant_profile.tenant_id == tenant_id).first()
    #         tenant_obj.subscription_status = 'inactive'
    #         # tenant_obj.subscription_plan = plan
    #     self.db.commit()
    #     return {"status":"success"}
        
        
def get_stripe_subscription_service(current_user = Depends(deps.get_current_user), db = Depends(get_db)):
    return StripeService(current_user=current_user, db=db)
def get_unauthorized_subscription_service( db = Depends(get_base_db)):
    return StripeService(current_user=None, db=db)
