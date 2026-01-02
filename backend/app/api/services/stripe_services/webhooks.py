import asyncio
import stripe
from .service_context import ServiceContext
from .service_context import ServiceContext
from fastapi import HTTPException, status, Depends
from app.db.database import get_db, get_base_db
from ...core import deps
from ...services.helper_service import *


class WebhookServices(ServiceContext):
    """This i is a tripe integration for riders checkout after booking"""
    def __init__(self, current_user, db):
        super().__init__(current_user, db)
        
    ##Maison subscription webhook
    async def webhook(self,request):
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
            return 
        logger.debug(f"webhook event")
        if event['type'] == 'checkout.session.completed' :
            ##Update status in db version
            session  =event['data']['object']
            
            tenant_id = session.get('metadata', {}).get('tenant_id')
            stripe_customer_id = session.get('customer')
            plan = session.get('metadata',{}).get('product_type')
            subscription_id = session.get('subscription')
            logger.debug(f"Tenant {tenant_id} successfully subscribed. customer_id [{stripe_customer_id}] paln [{plan}] sub_id [{subscription_id}]")
            tenant_obj:tenant_profile = self.db.query(tenant_profile).filter(tenant_profile.tenant_id == tenant_id).first()
            tenant_obj.subscription_status = 'active'
            tenant_obj.subscription_plan = plan
            tenant_obj.cur_subscription_id = subscription_id
            
        elif event['type'] == 'customer.subscription.updated':
            # session  =event['data']['object']
            subscription = event['data']['object']
    
            
            subscription_id = subscription.get('id')
            
            stripe_customer_id = subscription.get('customer')
            
            metadata = subscription.get('metadata', {})
            tenant_id = metadata.get('tenant_id')
            plan = metadata.get('product_type')
            logger.debug(f"Tenant {tenant_id} successfully subscribed. customer_id [{stripe_customer_id}] paln [{plan}] sub_id [{subscription_id}]")
            tenant_obj:tenant_profile = self.db.query(tenant_profile).filter(tenant_profile.tenant_id == tenant_id).first()
            tenant_obj.subscription_status = 'active'
            tenant_obj.subscription_plan = plan
            tenant_obj.cur_subscription_id = subscription_id
        elif event['type'] == 'invoice.paid':
            # this triggers on every renewal
            invoice = event['data']['object']
            subscription_id = invoice.get('subscription')
            logger.debug(f"Payment successfull for sub: {subscription_id}")
            
            # logger.debug(f"{invoice}")
            ##send email notifying
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            logger.debug(f"Subsripiton {subscription['id']} has ended.")
            tenant_obj:tenant_profile = self.db.query(tenant_profile).filter(tenant_profile.tenant_id == tenant_id).first()
            tenant_obj.subscription_status = 'inactive'
            # tenant_obj.subscription_plan = plan
        self.db.commit()
        return {"status":"success"}
      
    ##Tenant connect webhook   
    async def tenant_connect_webhooks(self, request):
        #To set things in play upon success or failed request: if tenant permits fare destrubtion
        try:
            payload = await request.body()
            webhook_secret = self.CONNECT_WEBHOOK_SECRET
            sig_header = request.headers.get("stripe-signature")
            # logger.info()
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                webhook_secret
            )
        except Exception as e:
            raise HTTPException(400)
        tenant_stripe_id = event.get('account')
        
        logger.debug(f"webhook event:[{event['type']}] for {tenant_stripe_id}")
        try:
            
            if event['type'] in ('account.updated' ,'account.created'):
                account = event['data']['object']
                metadata =  account.get('metadata', {})
                tenant_id = metadata.get('tenant_id')
                response:tenant_profile = self.db.query(tenant_profile).filter(tenant_profile.tenant_id == tenant_id).first()
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
                    response.charges_enabled = account.get('charges_enabled')
                    self.db.commit()    
                    
            elif event['type'] == 'checkout.session.completed' :
                session = event['data']['object']
                metadata = session.get('metadata', {})
                rider_id = metadata.get('rider_id')
                response:booking_table = self.db.query(booking_table).filter(booking_table.rider_id == rider_id)
                response.payment_status = 'paid'
                
                logger.info(f"Payment recieved for tenant {tenant_stripe_id}")
            elif event['type'] in ('payment_intent.succeeded'):
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
            return success_resp()
        
        except Exception as e:
            raise e
def get_ebhook_services(db = Depends(get_base_db)):
    
    return WebhookServices(current_user=None, db=db)