import stripe
from .service_context import ServiceContext
from .service_context import ServiceContext
from fastapi import HTTPException, status, Depends
from app.db.database import get_db, get_base_db
from ...core import deps
from ...services.helper_service import *
from app.domain.plans import PLAN_REGISTRY

class BookingCheckout(ServiceContext):
    """This i is a tripe integration for riders checkout after booking"""
    def __init__(self, current_user, db):
        super().__init__(current_user, db)
    def _is_deposit(self, booking_obj):
        tenant_response:tenant_setting_table = self.db.query(tenant_setting_table).filter(tenant_setting_table.tenant_id == self.tenant_id).first()
        # logger.debug(f"Config {tenant_response.__dict__}")
        config = tenant_response.config
        
        is_deposit = config['booking']['types'][booking_obj.service_type]['is_deposit_required']
        logger.debug(f"{booking_obj.service_type} deposit:{is_deposit}")
        return is_deposit
    async def checkout_session(self, booking_obj:booking_table,is_transfer: bool = None):
        """_summary_

        Args:
            booking_obj (booking_table)
            is_transfer (bool, optional): Transfer to drivers connect account. Defaults to None.

        Raises:
            e: _description_

        Returns:
            _type_: _description_
        """
        try:
           
            
            charges_status = booking_obj.tenant.profile.charges_enabled
            logger.debug(f"Tenant payment status {charges_status} ")
            if not booking_obj:
                    raise HTTPException(400, "booking_notfount")
            if charges_status:
                logger.debug(f"{booking_obj.tenant_id}")
                
                booking_id = booking_obj.id
                rider_id = booking_obj.rider_id
                tenant_stripe_acct_id = booking_obj.tenant.profile.stripe_account_id
        
                
                is_deposit = self._is_deposit(booking_obj=booking_obj)
                    
                
                unit_amount = self._to_cent(price=booking_obj.estimated_price)
                payment_type = 'full' if booking_obj.payment_status == 'pending' else 'balance'
              
                if payment_type == 'balance' and is_deposit:
                    balance = self._to_cent(booking_obj.estimated_price) - unit_amount
                    unit_amount = balance
                    logger.debug(f"Balance {balance}")
                if is_deposit:
                    payment_type = 'deposit' 
                    
                    unit_amount=self._get_deposit(booking_obj=booking_obj, unit_amount=unit_amount)
                    logger.debug(f"deposit {unit_amount}")
                customer_id = booking_obj.rider.stripe_customer_id
                if not customer_id:
                    customer_id = await self._create_stripe_cutstomer()
                #application fee
                calc =self._to_dollars(unit_amount) * PLAN_REGISTRY[self.sub_plan].maison_fee
                maison_fee = self._to_cent(calc)
                logger.debug(f"Maison fee {self._to_dollars(unit_amount) } * {PLAN_REGISTRY[self.sub_plan].maison_fee} = {maison_fee}") 
                confirm =False
                payment_id = None
                if self.role == 'driver':
                    confirm =True 
                    payment_id = booking_obj.payment_id
                intent =stripe.PaymentIntent.create(
                        amount=unit_amount,
                        currency='usd',
                        customer=customer_id,
                        application_fee_amount=maison_fee,
                        automatic_payment_methods={
                                "enabled": True,
                                "allow_redirects": "never",
                            },
                        # transfer_data={
                        #     "destination":tenant_stripe_acct_id,
                        # }, 
                        payment_method=payment_id,
                        metadata={
                            "rider_id": rider_id,
                            "tenant_id": self.tenant_id,
                            "payment_type":payment_type,
                            "booking_id":booking_id
                        },
                         # MISSING: these are critical
                        setup_future_usage="off_session",  # Save card for balance charges
                        confirm=confirm,  # Let frontend confirm (if using client_secret)
                       
                        description=f"Ride booking {booking_id} - {payment_type}",
                        
                        # Optional but usleful
                        receipt_email= booking_obj.rider.email,  # Send receipt
                        stripe_account=tenant_stripe_acct_id
                        
                    )
                # logger.debug(f"{intent}")
                _intent = stripe.PaymentIntent.retrieve( 
                            intent.id,
                            stripe_account=tenant_stripe_acct_id  
                            )
                logger.debug(f"{intent.metadata}")
                return success_resp(msg = "Success", data={"client_secret":_intent.client_secret, "payment_type":payment_type, "tenant_acct_id":tenant_stripe_acct_id})
                
                
         
            # if charges_status:
            #     session = stripe.checkout.Session.create(line_items=line_items,
            #                                         mode="payment",
            #                                         customer_email=obj_response.rider.email,
            #                                         stripe_account=tenant_stripe_acct_id,
            #                                         success_url=f"http://{slug}.{self.BASE_URL}/booking/complete",
            #                                         cancel_url= f"http://{slug}.{self.BASE_URL}/booking/failed",
                                                    
            #                                         payment_intent_data={
            #                                             "application_fee_amount": maison_fee
            #                                         },
            #                                         metadata={"rider_id": rider_id}
            #                                         )
            
            #     return success_resp(msg = "Success", data={"checkout_session":session.url, "line_items": line_items})
            else:
                logger.debug(f"Tenant cananot take charges. Charges:-> {charges_status} ")
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
            
           

        except Exception as e:
            raise e
    
    def _get_deposit(self, booking_obj: object, unit_amount):
        #calculate deposit if deposit
            
            booking_config:tenant_booking_price = self.db.query(tenant_booking_price).filter(tenant_booking_price.tenant_id == self.tenant_id,
                                                                                                tenant_booking_price.service_type == booking_obj.service_type).first()
                                
            deposit_fee= booking_config.deposit_fee
            deposit_type = booking_config.deposit_type  ## unit_amount * %
            if deposit_type == "percentage":
                deposit = booking_obj.estimated_price * deposit_fee
                logger.debug(f"Deposit {deposit}")
                deposit_cents = self._to_cent(deposit)
                logger.debug(f"Deposit {deposit_cents}")
                
                return deposit_cents
            elif deposit_type == "flat":
                return self._to_cent(price=deposit_fee)
            else:
                raise ValueError("Deposit type not valid")
    async def _create_stripe_cutstomer(self):
        try:
            customer = stripe.Customer.create(
                email=self.current_user.email,
                name=self.current_user.full_name,
                metadata={
                    "tenant_id": self.current_user.tenant_id,
                    "rider_id": id,
                },
                stripe_account=self.current_user.tenants.profile.stripe_account_id
            )
            return customer.id
        except Exception as e:
            raise e
    async def _get_line_items(self, booking: booking_table, product_data: dict = None):
        try:
            
            logger.debug(f"Booking: {booking.rider.full_name}")
            pickup_time = booking.pickup_time
            product_name = f"Private Car Service: {booking.pickup_location} to {booking.dropoff_location}"
            product_description = (
                                f"Date: {pickup_time} | Vehicle: {booking.vehicle.vehicle_name}\n"
                                f"Passenger: {booking.rider.full_name}\n"
                                f"Notes: {booking.notes}"
                            )
            _product_data = {}
            if not product_data:
                _product_data['name'] = product_name
                _product_data['description'] = product_description
            else: _product_data = product_data
            
            unit_amount = self._to_cent(price = booking.estimated_price)
            
            line_items=[
            {
            "price_data": {
                "currency": "usd",
                "product_data": _product_data,
                "unit_amount": unit_amount, # The real-time sum you calculated
            },
            "quantity": 1,
            },
            ]
            return line_items
        except Exception as e:
            raise e 
    def _to_cent(self, price):
        try: # *100
            to_cent = int(price * 100)
            return to_cent
        except Exception as e:
            raise e     
        
    def _to_dollars(self, price):
        try: # *100
            to_cent = int(price / 100)
            return to_cent
        except Exception as e:
            raise e   
def get_checkout_service(db = Depends(get_db), current_user = Depends(deps.get_current_user)):
    return BookingCheckout(current_user=current_user,
                    db=db)
def get_unauthorized_checkout_service(db = Depends(get_base_db)):
    return BookingCheckout(current_user=None, db=db)