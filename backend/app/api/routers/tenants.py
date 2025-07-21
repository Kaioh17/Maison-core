from typing import Optional
from fastapi import APIRouter, HTTPException, FastAPI, Query, Response, status
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from ..services import tenants_service
from app.schemas import tenant, driver, vehicle, booking
from ..core import oauth2
from app.utils.logging import logger

router = APIRouter(
    prefix="/api/v1/tenant",
    tags=['Tenant']
)

# Get tenant's company info
@router.get('/', status_code=status.HTTP_200_OK, response_model=tenant.TenantResponse)
def tenants(db: Session = Depends(get_db), current_tenants: int = Depends(oauth2.get_current_user)):
    logger.info("Tenant's info")
    company = tenants_service.get_company_info(db, current_tenants)
    return company

# Create a new tenant
@router.post('/add', status_code=status.HTTP_201_CREATED, response_model=tenant.TenantResponse)
def create_tenants(payload: tenant.TenantCreate, db: Session = Depends(get_db)):
    logger.info("Tenants created")
    tenant_obj = tenants_service.create_tenant(db, payload)
    return tenant_obj

# Get all drivers for the current tenant
@router.get('/drivers', status_code=status.HTTP_200_OK, response_model=list[driver.DriverResponse])
async def get_drivers(db: Session = Depends(get_db), current_tenants: int = Depends(oauth2.get_current_user)):
    logger.info("Tenant drivers")
    drivers = await tenants_service.get_all_drivers(db, current_tenants)
    return drivers

# Get vehicles for the tenant, optionally filtered by driver or assignment
@router.get('/vehicles', status_code=status.HTTP_200_OK, response_model=list[vehicle.VehicleResponse])
async def get_vehicles(
    driver_id: Optional[int] = Query(None, description="Get vehicles for specific driver"),
    assigned_drivers: Optional[bool] = Query(False, description="Get only vehicles assigned to drivers"),
    db: Session = Depends(get_db),
    current_tenants: int = Depends(oauth2.get_current_user)
):
    if assigned_drivers:
        logger.info("Getting vehicles assigned to drivers")
        vehicles = await tenants_service.fetch_assigned_drivers_vehicles(db, current_tenants)
    elif driver_id:
        logger.info(f"Getting driver [{driver_id}] vehicles...")
        vehicles = await tenants_service.find_vehicles_owned_by_driver(db, driver_id, current_tenants)
    else:
        logger.info("Tenant vehicles...")
        vehicles = await tenants_service.get_all_vehicles(db, current_tenants)
    return vehicles

# Get bookings for the tenant, optionally filtered by status
@router.get('/bookings', status_code=status.HTTP_200_OK, response_model=list[booking.BookingRespose])
async def get_bookings(
    booking_status: Optional[str] = Query(None, description="only this labels can be passed 'pending', 'confirmed', 'active', 'cancelled', 'no_show'"),
    db: Session = Depends(get_db),
    current_tenant: int = Depends(oauth2.get_current_user)
):
    if booking_status:
        logger.info(f"Getting {booking_status} bookings...")
        bookings = await tenants_service.get_bookings_by_status(db, booking_status, current_tenant)
    else:
        logger.info(f"All available bookings for {current_tenant.id}")
        bookings = await tenants_service.get_all_bookings(db, current_tenant)
    return bookings

# Onboard a new driver for the tenant
@router.post('/onboard', status_code=status.HTTP_201_CREATED, response_model=tenant.OnboardDriverResponse)
async def onboard_drivers(
    payload: tenant.OnboardDriver,
    db: Session = Depends(get_db),
    current_tenant: int = Depends(oauth2.get_current_user)
):
    logger.info("Onboarding driver...")
    new_driver = await tenants_service.onboard_drivers(db, payload, current_tenant)
    return new_driver

# # Update tenant settings (future implementation)
# @router.patch('/settings', status_code=status.HTTP_202_ACCEPTED)
# async def update_settings(db: Session):
#     pass