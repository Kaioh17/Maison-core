from fastapi import APIRouter, HTTPException, FastAPI, Response,status, Query
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db, get_base_db
from ..services import driver_service, stripe_tier_services
from app.schemas import driver, booking, general, subscription
from ..core import deps
from .dependencies import is_tenants
from typing import Optional
from app.utils.logging import logger
from app.models import Tenants


router = APIRouter(
    prefix = "/api/v1/subscription",
    tags = ["Subscription"]
)


@router.post("/")
async def create_subscription(payload: subscription.SubscriptionCreate,
                              db: Session = Depends(get_db),
                            current_user = Depends(deps.get_current_user),
                            is_tenant = Depends(is_tenants)):
    logger.info(f"{current_user.slug} get customer")
    get_customer = db.query(Tenants).filter(Tenants.id == current_user.id).first()
    
    create_subscription = await stripe_tier_services.StripeService.create_subscription(customer_id= get_customer.stripe_customer_id,  price_id=payload.price_id)
    return create_subscription

@router.get("/{customer_id}")
async def get_subscription(db: Session = Depends(get_db)):
    get_subscription_status = await stripe_tier_services.StripeService.get_customer_subscription_status()
    return {"status": get_subscription_status}