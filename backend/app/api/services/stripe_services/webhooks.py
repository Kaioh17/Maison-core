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
        Anything else (checkout.session.*, payment.created) is acknowledged and ignored.
        Payment events are only applied when event['account'] is the tenant that owns the booking.

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
                self._handle_account_event(event, tenant_stripe_id)
            elif event['type'] in ('payment_intent.succeeded', 'charge.succeeded'):
                self._handle_payment_succeeded(event, tenant_stripe_id)
            else:
                # checkout.session.* / payment.created are not part of the booking flow (riders pay with
                # PaymentIntents), so they are acknowledged and ignored.
                logger.info(f"[connect webhook] unhandled event type {event['type']}, ignoring")
            return success_resp()
        
        except Exception as e:
            self.db.rollback()
            raise e

    # Bookings only ever move forward: a late or replayed 'deposit' event must not undo a 'full' payment.
    _PAYMENT_RANK = {'pending': 0, 'deposit_paid': 1, 'balance_paid': 2, 'full_paid': 2}
    _PAYMENT_STATUS = {'deposit': 'deposit_paid', 'balance': 'balance_paid', 'full': 'full_paid'}

    def _handle_account_event(self, event, tenant_stripe_id):
        account = event['data']['object']
        tenant_id = (account.get('metadata') or {}).get('tenant_id')
        if not tenant_stripe_id or account.get('id') != tenant_stripe_id:
            logger.warning(f"[connect webhook] account event {event.get('id')} account mismatch, ignoring")
            return

        profile = self.db.query(tenant_profile).filter(tenant_profile.tenant_id == tenant_id).first() if tenant_id else None
        if not profile:
            raise HTTPException(404, "Tenant not found!")
        # A tenant is bound to one connected account. Re-pointing it would redirect that tenant's payouts.
        if profile.stripe_account_id and profile.stripe_account_id != tenant_stripe_id:
            logger.error(f"[connect webhook] tenant {tenant_id} already linked to a different Stripe account, ignoring {event.get('id')}")
            return

        profile.charges_enabled = bool(account.get('charges_enabled'))
        if account.get('charges_enabled'):
            profile.stripe_account_id = tenant_stripe_id
            tenant_obj = self.db.query(tenant_table).filter(tenant_table.id == tenant_id).first()
            if tenant_obj:
                tenant_obj.is_verified = True
                tenant_obj.is_active = True
            logger.info(f"Tenant {tenant_id} can now accept charges")
        self.db.commit()

    def _handle_payment_succeeded(self, event, tenant_stripe_id):
        intent = event['data']['object']
        metadata = intent.get('metadata') or {}
        rider_id, booking_id = metadata.get('rider_id'), metadata.get('booking_id')
        payment_type = (metadata.get('payment_type') or '').lower()
        intent_id = intent.get('id')
        if not (rider_id and booking_id and payment_type in self._PAYMENT_STATUS):
            # e.g. a payment made on the connected account outside Maison's booking flow
            logger.info(f"[connect webhook] {intent_id} has no Maison booking metadata, ignoring")
            return

        booking = self.db.query(booking_table).filter(booking_table.rider_id == rider_id,
                                                      booking_table.id == booking_id).first()
        if not booking:
            logger.debug("booking not found")
            raise HTTPException(404)

        # Connect events are signed by Stripe but their metadata is not ours to trust: it can be set by whoever
        # created the payment on that account. The event must come from the tenant that owns the booking.
        owner_account = booking.tenant.profile.stripe_account_id if booking.tenant and booking.tenant.profile else None
        if not owner_account or owner_account != tenant_stripe_id:
            logger.error(f"[connect webhook] SECURITY: {intent_id} from account {tenant_stripe_id} "
                         f"claims booking {booking.id} owned by {owner_account}; ignoring")
            return
        if metadata.get('tenant_id') not in (None, str(booking.tenant_id)):
            logger.error(f"[connect webhook] SECURITY: {intent_id} tenant metadata does not match booking {booking.id}; ignoring")
            return
        amount = intent.get('amount')
        total_cents = int(round((booking.estimated_price or 0) * 100))
        if not isinstance(amount, int) or amount <= 0 or (total_cents and amount > total_cents):
            logger.error(f"[connect webhook] SECURITY: {intent_id} amount {amount} outside 1..{total_cents} for booking {booking.id}; ignoring")
            return

        if intent_id in (booking.deposit_intent_id, booking.balance_intent_id):
            return  # already recorded (payment_intent.succeeded and charge.succeeded both arrive)

        rider_obj = self.db.query(user_table).filter(user_table.id == rider_id).first()
        if not rider_obj:
            raise HTTPException(404)
        customer_id = intent.get('customer')
        if customer_id:
            if not rider_obj.stripe_customer_id:
                rider_obj.stripe_customer_id = customer_id
            elif rider_obj.stripe_customer_id != customer_id:
                raise HTTPException(status.HTTP_409_CONFLICT, "Customer ids do not match")

        new_status = self._PAYMENT_STATUS[payment_type]
        if self._PAYMENT_RANK.get(booking.payment_status or 'pending', 0) <= self._PAYMENT_RANK[new_status]:
            booking.payment_status = new_status
        if payment_type == 'deposit':
            booking.deposit_intent_id = intent_id
        else:
            booking.balance_intent_id = intent_id
        if intent.get('payment_method'):
            booking.payment_id = intent['payment_method']
        self.db.commit()
        logger.info(f"Payment [{intent_id}] recorded for booking {booking.id}")


def get_ebhook_services(db = Depends(get_base_db)):
    """Dependency: webhook routes use base DB session; no logged-in user (Stripe signs requests)."""
    
    return WebhookServices(current_user=None, db=db)
