"""
Stripe webhook handlers (HTTP layer lives in api/routers/webhooks.py).

Two pipelines — keep them separate in Stripe Dashboard:

1) webhook() — WEBHOOK_SECRET
   Platform / billing: Maison tenant subscriptions (checkout.session.completed,
   customer.subscription.*, invoice.paid, etc.). Updates tenant_profile subscription fields.

2) tenant_connect_webhooks() — CONNECT_WEBHOOK_SECRET
   Stripe Connect: connected account id on each event (event['account']). Handles
   account.created / account.updated to persist stripe_account_id and charges_enabled
   on tenant_profile after Express onboarding; also booking payments on connected accounts.
"""
import asyncio
import stripe
from .service_context import ServiceContext
from .service_context import ServiceContext
from fastapi import HTTPException, status, Depends
from app.db.database import get_db, get_base_db
from ...core import deps
from ...services.helper_service import *
from .stripe_service import StripeService
from ...services.email_services.tenants import TenantEmailServices
from app.domain.billing import price_to_plan
from app.domain.plans import PlanName, SubStatus, resolve_plan, resolve_status

class WebhookServices(ServiceContext):
    """
    Stripe webhook business logic. Stateless requests: current_user is None;
    auth is via stripe-signature header + the appropriate webhook secret.
    """
    def __init__(self, current_user, db):
        super().__init__(current_user, db)

    def _find_tenant_profile(self, tenant_id, stripe_customer_id):
        """Locate a tenant profile by metadata tenant_id, falling back to customer id."""
        tenant_obj = None
        if tenant_id is not None:
            tenant_obj = self.db.query(tenant_profile).filter(
                tenant_profile.tenant_id == tenant_id
            ).first()
        if tenant_obj is None and stripe_customer_id:
            tenant_obj = self.db.query(tenant_profile).filter(
                tenant_profile.stripe_customer_id == stripe_customer_id
            ).first()
        return tenant_obj

    def _retrieve_subscription(self, subscription_id):
        if not subscription_id:
            return None
        try:
            return stripe.Subscription.retrieve(
                subscription_id, expand=["items.data.price"]
            )
        except Exception as e:
            logger.warning(f"Could not retrieve subscription {subscription_id}: {e}")
            return None

    def _derive_plan(self, subscription, metadata):
        """Resolve the plan from the price actually purchased.

        Metadata is editable from the Stripe dashboard and is set by whatever
        created the session, so it is not authoritative. We prefer the price id
        on the subscription and only fall back to metadata if that is
        unavailable, logging loudly when the two disagree.
        """
        claimed = (metadata or {}).get('product_type')
        derived = None
        try:
            items = (subscription or {}).get('items', {}).get('data', [])
            if items:
                price_id = items[0].get('price', {}).get('id')
                derived = price_to_plan(price_id)
        except Exception as e:
            logger.warning(f"Could not derive plan from subscription price: {e}")

        if derived is None:
            logger.warning(
                f"Falling back to metadata plan '{claimed}' -- could not derive "
                "plan from the Stripe price."
            )
            return resolve_plan(claimed).name
        if claimed and claimed.strip().lower() != derived:
            logger.error(
                f"Plan mismatch: metadata claims '{claimed}' but the purchased "
                f"price maps to '{derived}'. Using '{derived}'."
            )
        return derived

    # --- Main platform webhook (WEBHOOK_SECRET): subscriptions & platform checkout ---
    async def webhook(self,request):
        """
        Process events signed with WEBHOOK_SECRET (platform webhook endpoint).

        Intended events:
        - checkout.session.completed: tenant subscribed — set subscription_status, plan, cur_subscription_id
        - customer.subscription.updated: sync subscription metadata to tenant_profile
        - invoice.paid: renewal logging (extend as needed)
        - customer.subscription.deleted: mark subscription inactive

        Does NOT handle Connect account onboarding; use tenant_connect_webhooks for that.
        """
        try:
            payload = await request.body()
            webhook_secret = self.WEBHOOK_SECRET
            sig_header = request.headers.get("stripe-signature")
            # logger.info()
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                webhook_secret
            )
        except Exception as e:
            logger.error(f"[webhook] signature/payload verification failed: {e}")
            raise HTTPException(400)

        if event['type'] == 'checkout.session.completed' :
            ##Update status in db version
            session  =event['data']['object']

            tenant_id = session.get('metadata', {}).get('tenant_id')
            stripe_customer_id = session.get('customer')
            subscription_id = session.get('subscription')
            # The session carries no status and its metadata is not trustworthy,
            # so read both off the subscription itself.
            sub_obj = self._retrieve_subscription(subscription_id)
            plan = self._derive_plan(sub_obj, session.get('metadata', {}))
            sub_status = resolve_status(sub_obj.get('status') if sub_obj else SubStatus.ACTIVE.value)
            logger.debug(f"Tenant {tenant_id} successfully subscribed. customer_id [{stripe_customer_id}] plan [{plan}] status [{sub_status}] sub_id [{subscription_id}]")
            tenant_obj = self._find_tenant_profile(tenant_id, stripe_customer_id)
            if tenant_obj is None:
                logger.warning(
                    f"checkout.session.completed for unknown tenant_id={tenant_id} "
                    f"customer_id={stripe_customer_id}. Skipping."
                )
                return {"status": "success"}
            tenant_obj.subscription_status = sub_status
            tenant_obj.subscription_plan = plan
            tenant_obj.cur_subscription_id = subscription_id

            # Send subscription confirmation + the "one step left to go live"
            # welcome email (Stripe verification is the remaining step).
            try:
                tenant_info = self.db.query(tenant_table).filter(tenant_table.id == int(tenant_id)).first()
                if tenant_info:
                    email_service = TenantEmailServices(
                        to_email=tenant_info.email,
                        from_email='noreply',
                        display_name=tenant_obj.slug or 'Maison',
                    )
                    email_service.subscription_confirmation_email(tenant_obj=tenant_info, plan=plan)
                    email_service.welcome_email(obj=tenant_info, slug=tenant_obj.slug)
            except Exception as email_err:
                logger.warning(f"Subscription email failed for tenant {tenant_id}: {email_err}")

        elif event['type'] in ('customer.subscription.updated', 'customer.subscription.created'):
            subscription = event['data']['object']

            subscription_id = subscription.get('id')
            stripe_customer_id = subscription.get('customer')
            metadata = subscription.get('metadata', {})
            tenant_id = metadata.get('tenant_id')
            plan = self._derive_plan(subscription, metadata)
            event_id = event.get('id')

            logger.info(
                f"[webhooks] {event['type']}: looking up tenant_profile "
                f"tenant_id={tenant_id} customer_id={stripe_customer_id} event_id={event_id}"
            )
            tenant_obj = self._find_tenant_profile(tenant_id, stripe_customer_id)

            if tenant_obj is None:
                logger.warning(
                    f"{event['type']} received but no tenant found for "
                    f"customer_id={stripe_customer_id} tenant_id={tenant_id}. "
                    f"Event ID: {event_id}. Skipping."
                )
                return {"status": "success"}

            # Store Stripe's own status rather than hardcoding 'active', so
            # trialing / past_due / unpaid / incomplete are represented faithfully.
            tenant_obj.subscription_status = resolve_status(subscription.get('status'))
            tenant_obj.subscription_plan = plan
            tenant_obj.cur_subscription_id = subscription_id
        elif event['type'] in ('invoice.paid', 'invoice.finalized', 'invoice.payment_succeded'):
            # this triggers on every renewal
            invoice = event['data']['object']
            subscription_id = invoice.get('subscription')
            logger.debug(f"Payment successfull for sub: {subscription_id}")

            # logger.debug(f"{invoice}")
            ##send email notifying
        elif event['type'] == 'invoice.payment_failed':
            # Reflect the failure before Stripe transitions the subscription, so
            # the state is visible in the limits endpoint. past_due is still
            # entitled -- this is the grace period, not a cut-off.
            invoice = event['data']['object']
            tenant_obj = self._find_tenant_profile(None, invoice.get('customer'))
            if tenant_obj is not None:
                logger.info(f"Payment failed for customer {invoice.get('customer')}; marking past_due")
                tenant_obj.subscription_status = SubStatus.PAST_DUE.value
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            logger.debug(f"Subscription {subscription['id']} has ended.")
            # tenant_id was never assigned in this branch before, so every
            # cancellation raised NameError and the tenant stayed entitled.
            tenant_obj = self._find_tenant_profile(
                subscription.get('metadata', {}).get('tenant_id'),
                subscription.get('customer'),
            )
            if tenant_obj is None:
                logger.warning(
                    f"customer.subscription.deleted for unknown customer "
                    f"{subscription.get('customer')}. Skipping."
                )
                return {"status": "success"}
            tenant_obj.subscription_status = resolve_status(subscription.get('status')) \
                if subscription.get('status') else SubStatus.CANCELED.value
            tenant_obj.subscription_plan = PlanName.FREE.value
            tenant_obj.cur_subscription_id = None
        else:
            # Nothing mutated; skip the commit entirely.
            logger.info(f"[webhook] unhandled event type {event['type']}, ignoring")
            return {"status": "success"}

        try:
            self.db.commit()
        except Exception as e:
            logger.error(f"Webhook commit failed for {event['type']}: {e}")
            self.db.rollback()
            raise
        return {"status":"success"}
      
    # --- Connect webhook (CONNECT_WEBHOOK_SECRET): Express accounts + Connect payments ---
    async def tenant_connect_webhooks(self, request):
        """
        Process events signed with CONNECT_WEBHOOK_SECRET (Connect webhook endpoint).

        - account.created / account.updated / v1.account.updated: read metadata.tenant_id; when charges_enabled,
          set tenant_profile.stripe_account_id from event['account'], charges_enabled, and
          mark tenant verified/active.
        - payment_intent.succeeded / charge.succeeded: update booking payment_status from metadata.
        - checkout.session.completed (Connect context): rider checkout updates (see handler).

        event['account'] is the connected account ID (acct_...) for Connect events.
        """
        #To set things in play upon success or failed request: if tenant permits fare destrubtion
        try:
            logger.info(f"[tenant connect webhooks]")
            payload = await request.body()
            webhook_secret = self.CONNECT_WEBHOOK_SECRET
            sig_header = request.headers.get("stripe-signature")
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                webhook_secret
            )
            
        except Exception as e:
            raise HTTPException(400)
        tenant_stripe_id = event.get('account')
        
        logger.info(f"webhook event:[{event['type']}] for {tenant_stripe_id}")
        try:
            
            if event['type'] in ('account.updated' ,'account.created', 'v1.account.updated'):
                logger.debug(event['type'])
                # Persist Connect account id on tenant_profile once charges can be collected
                account = event['data']['object']
                logger.info(f"[DEBUG] [webhooks] Account is: {account}")
                
                metadata =  account.get('metadata', {})
                logger.info(f"[DEBUG] [webhooks] Metadata: {metadata}")
                tenant_id = metadata.get('tenant_id')
                logger.info(f"[DEBUG] [webhooks] Tenant_id: {tenant_id}")
                
                response:tenant_profile = self.db.query(tenant_profile).filter(tenant_profile.tenant_id == tenant_id).first()
                
                if not response:
                    raise HTTPException(404, "Tenant not found!")
                logger.info(f"[DEBUG] [webhooks] respose: {response}")
                
                tenant_response:tenant_table = self.db.query(tenant_table).filter(tenant_table.id == tenant_id).first()
                
                if account.get('charges_enabled'):
                    logger.debug(f"Tenant account status is {account.get('charges_enabled')}  q(≧▽≦q)")
                    
                    
                    response.stripe_account_id = tenant_stripe_id
                    response.charges_enabled = account.get('charges_enabled')
                    tenant_response.is_verified = True
                    tenant_response.is_active = True
                    
                    self.db.commit()
                    logger.info(f"Tenant {tenant_stripe_id} is now ready to make some cash q(≧▽≦q)")
                else:
                    # Onboarding not finished — still save charges_enabled flag
                    response.charges_enabled = account.get('charges_enabled')
                    self.db.commit()   
             
                
            elif event['type'] == 'checkout.session.completed' :
                session = event['data']['object']
                metadata = session.get('metadata', {})
                rider_id = metadata.get('rider_id')
                response:booking_table = self.db.query(booking_table).filter(booking_table.rider_id == rider_id)
                response.payment_status = 'paid'
                
                logger.info(f"Payment recieved for tenant {tenant_stripe_id}")
            elif event['type'] in ('payment_intent.succeeded', 'charge.succeeded'):
                try:
                    logger.debug("Payment succeeded")
                    status_dict = {
                                    'deposit': 'deposit_paid',
                                    'balance': 'balance_paid',
                                    'full': 'full_paid'
                                }
                    intent = event['data']['object']
                    logger.debug(f"Webhook object type {intent.get('object')}")
                    
                    
                    customer_id = intent['customer'] 
                    intent_id = intent['id']
                    payment_id = intent['payment_method']
                    metadata = intent.get('metadata', {})
                    rider_id = metadata.get('rider_id')
                    payment_type:str = metadata.get('payment_type')
                    booking_id = metadata.get('booking_id')
                    logger.debug(f"Rider {rider_id}")
                    logger.debug(f"Meta {metadata}")
                    
                    # await asyncio.sleep(60)
                    
                    response:booking_table = self.db.query(booking_table).filter(booking_table.rider_id == rider_id,
                                                                                booking_table.id == booking_id ).first()
                    #Verify customer id or add new
                    if not response:
                        logger.debug(f"booking NOt found")
                        raise HTTPException(404)
                    logger.debug(response.__dict__)
                    
                    rider_obj:user_table =  self.db.query(user_table).filter(user_table.id == rider_id).first()
                    if not rider_obj:
                        logger.debug(f"booking NOt found")
                        raise HTTPException(404)
                    
                    if not rider_obj.stripe_customer_id:
                        rider_obj.stripe_customer_id = customer_id
                    elif rider_obj.stripe_customer_id != customer_id:
                        raise HTTPException(status.HTTP_409_CONFLICT, "Customer ids do not match")
                    response.payment_status = status_dict[payment_type.lower()]
                
                    if payment_type == 'deposit':
                        response.deposit_intent_id = intent_id
                    elif payment_type in ('balance', 'full'):
                      
                        
                        response.balance_intent_id = intent_id
                    
                    response.payment_id = payment_id
                    
                    self.db.commit()
                    logger.info(f"Payment [{intent_id}] recieved for tenant {tenant_stripe_id}")
                except Exception as e:
                    raise e    
            elif event['type'] == 'payment.created':
                logger.debug("Charge succeeded")
                status_dict = {
                                'deposit': 'deposit_paid',
                                'balance': 'balance_paid',
                                'full': 'full_paid'
                               }
                intent = event['data']['object']
              
                logger.debug(f"Webhook object type {intent.get('object')}")
                
                if intent.get('payment_intent'):
                    payment_intent = stripe.PaymentIntent.retrieve(
                        intent['payment_intent'],
                        stripe_account=tenant_stripe_id # Important for Connect
                    )
                    metadata = payment_intent.get('metadata', {})
                    logger.debug(f'Meta {metadata}')
                customer_id = intent['customer'] 
                intent_id = intent['id']

                metadata = intent.get('metadata', {})
                rider_id = metadata.get('rider_id')
                payment_type:str = metadata.get('payment_type')
                
                logger.debug(f"Rider {rider_id}")
                logger.debug(f"Meta {metadata}")
              
                logger.info(f"Charge [{intent_id}] recieved for tenant {tenant_stripe_id}")
                
                
            elif event['type'] == 'checkout.session.failed':
                pass
            else:
                logger.info(f"[connect webhook] unhandled event type {event['type']}, ignoring")
            return success_resp()
        
        except Exception as e:
            raise e
def get_ebhook_services(db = Depends(get_base_db)):
    """Dependency: webhook routes use base DB session; no logged-in user (Stripe signs requests)."""
    
    return WebhookServices(current_user=None, db=db)
