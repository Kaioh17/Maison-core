from fastapi import APIRouter, HTTPException, FastAPI, Request, Response,status, Query
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db, get_base_db
# from ..services import driver_service, stripe_tier_services
from app.schemas import driver, booking, general, subscription
from ..core import deps
from .dependencies import is_tenants
from typing import Dict, Optional
from app.utils.logging import logger
from app.models import Tenants
from ..services.stripe_services import stripe_service, stripe_tier_service
from ..services.stripe_services.stripe_tier_service import StripeService, get_stripe_subscription_service, get_unauthorized_subscription_service
router = APIRouter(
    prefix = "/api/v1/subscription",
    tags = ["Subscription"]
)



@router.post("/",status_code=status.HTTP_201_CREATED, response_model=general.StandardResponse[subscription.CheckoutSessionResponse])
async def create_checkout_session(payload: subscription.SubscriptionCreate,
                                stripe_service: StripeService = Depends(get_stripe_subscription_service),
                                is_tenant = Depends(is_tenants)):
    # logger.info(f"{current_user.slug} get customer")
    # get_customer = db.query(Tenants).filter(Tenants.id == current_user.id).first()
    
    create_subscription = await stripe_service.create_checkout_session(price_id=payload.price_id, product_type=payload.product_type)
    return create_subscription

@router.patch("/",status_code=status.HTTP_201_CREATED, response_model=general.StandardResponse[subscription.CheckoutSessionResponse])
async def upgrade_subscripton(payload: subscription.SubscriptionCreate,
                                stripe_service: StripeService = Depends(get_stripe_subscription_service),
                                is_tenant = Depends(is_tenants)):
    # logger.info(f"{current_user.slug} get customer")
    # get_customer = db.query(Tenants).filter(Tenants.id == current_user.id).first()
    
    upgrade_sub = await stripe_service.upgrade_subscription(price_id=payload.price_id ,product_type=payload.product_type)
    return upgrade_sub
@router.get("/{customer_id}")
async def get_subscription(db: Session = Depends(get_db)):
    get_subscription_status = await stripe_tier_service.StripeService.get_customer_subscription_status()
    return {"status": get_subscription_status}

@router.post("/webhooks", status_code=status.HTTP_201_CREATED)
async def stripe_webooks(request: Request, stripe_service: StripeService = Depends(get_unauthorized_subscription_service),):
    webhooks = await stripe_service.webhook(request)
    return webhooks