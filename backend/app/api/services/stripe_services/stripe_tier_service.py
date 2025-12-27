import stripe
from app.config import Settings
from .service_context import ServiceContext
from fastapi import HTTPException, status, Depends
from app.db.database import get_db, get_base_db
from ...core import deps
from app.models import user, driver, tenant
from app.utils import password_utils, db_error_handler
from app.utils.logging import logger
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

    async def create_checkout_session(self, price_id, product_type):
        try: 
            logger.info(f"{self.current_user.slug} get customer")
            get_customer = self.db.query(tenant_profile).filter(tenant_profile.tenant_id == self.current_user.id).first()
            # valid = Validations._tenants_exist(get_customer)
            customer_id = get_customer.stripe_customer_id
            logger.info(f" creating checkout seqssion {customer_id} ")
            
            checkout_session = stripe.checkout.Session.create(
                line_items=[{
                    'price': price_id,
                    'quantity':1
                }],
                mode='subscription',
                success_url= f"{self.BASE_URL}/success",
                cancel_url= f"{self.BASE_URL}/cancel",
                metadata= {
                    'tenant_id': self.current_user.id,
                    'product_type': product_type.lower()
                },
                customer=customer_id
            )
            # logger.debug(checkout_session)
            
            return success_resp(msg = "Successfully created checkout session", 
                                data = {'Checkout_session_url':checkout_session.url,
                                        'tenant_id': self.current_user.id,
                                        'customer_id': checkout_session.customer,
                                        'product_type': product_type,
                                        'sub_total': checkout_session.amount_subtotal},
                                )
        except Exception as e:
            return
        
    async def upgrade_subscription(self,price_id, product_type):
        """Use to upgrade subscrition"""
        try: 
            logger.info(f"{self.current_user.slug} get customer")
            get_customer = self.db.query(tenant_profile).filter(tenant_profile.tenant_id == self.current_user.id).first()
            # valid = Validations._tenants_exist(get_customer)
            customer_id = get_customer.stripe_customer_id
            current_sub_id = get_customer.cur_subscription_id
            logger.info(f" creating checkout session {customer_id} ")
            subscription = stripe.Subscription.retrieve(current_sub_id)
            sub_item_id = subscription['items']['data'][0].id
            checkout_session =  stripe.Subscription.modify(
                                current_sub_id,
                                # proration_behavior="create_prorations",
                                items=[{
                                    "id": sub_item_id,
                                    "price": price_id
                                }],
                                proration_behavior="always_invoice", # This bills them immediately for the difference
                                metadata= {
                                    'tenant_id': self.current_user.id,
                                    'product_type': product_type.lower()
                                },
                                )
            # eckoutch_session = stripe.checkout.Session.create(
            #                         line_items=[{
            #                             'price': price_id,
            #                             'quantity':1
            #                         }],
            #                         mode='subscription',
                                    
            #                         success_url= f"{self.BASE_URL}/upgrade/success",
            #                         cancel_url= f"{self.BASE_URL}/cancel",
            #                         metadata= {
            #                             'tenant_id': self.current_user.id,
            #                             'product_type': product_type.lower()
            #                         },
            #                         ##This is for upgrade
            #                         # setup_intent_data={
            #                         #      'proration_behavior':'always_invoice',
            #                         #     'metadata': {'subscription_id': current_sub_id},
            #                         # },
            #                         subscription_data={
                                        
            #                             'metadata': {
            #                                 'upgrading_from': current_sub_id # Old sub ID
            #                             }
            #                         },
            #                         customer=customer_id,
            #                         # Use to handle smoothly
            #                         # payment_behavior='allow_incomplete',
                                   
            #                         payment_method_collection='always'
            #                     )
            # logger.debug("done")
            # return checkout_session.url
            return success_resp(msg = "Upgraded checkout session", 
                                data = {'Checkout_session_url':checkout_session.url,
                                        'tenant_id': self.current_user.id,
                                        'customer_id': checkout_session.customer,
                                        'product_type': product_type,
                                       },
                                )
        except Exception as e:
            raise e
    
    async def get_customer_subscription_status(customer_id):
        subs = stripe.Subscription.list(customer=customer_id, limit =1)
        if subs.data:
            return subs.data[0].status 
        return None
    

    
    
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
        
        
def get_stripe_subscription_service(current_user = Depends(deps.get_current_user), db = Depends(get_db)):
    return StripeService(current_user=current_user, db=db)
def get_unauthorized_subscription_service( db = Depends(get_base_db)):
    return StripeService(current_user=None, db=db)