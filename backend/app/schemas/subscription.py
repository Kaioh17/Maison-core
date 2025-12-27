from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional
from .vehicle_config import VehicleConfigResponse
from .vehicle import VehicleResponse, VehicleCreate

class SubscriptionCreate(BaseModel):
    price_id: str
    product_type: str
    
class CheckoutSessionResponse(BaseModel):
    # 'Checkout_session_url':checkout_session.url,
    #                                     'tenant_id': self.current_user.id,
    #                                     'customer_id': checkout_session.customer,
    #                                     'product_type': product_type,
    #                                     'sub_total': checkout_session.amount_subtotal}
    
    Checkout_session_url: str
    tenant_id: int
    customer_id: str
    product_type: str
    sub_total: int