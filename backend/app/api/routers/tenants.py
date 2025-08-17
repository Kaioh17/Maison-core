from typing import Optional
from fastapi import APIRouter, HTTPException, FastAPI, Query, Response, status, Request
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db, get_base_db
from ..core import deps
from ..services import tenants_service
from app.schemas import tenant, driver, vehicle, booking, general
from ..core import security, deps
from app.utils.logging import logger

# from .dependencies import get_tenant_id_from_token 

router = APIRouter(
    prefix="/api/v1/tenant",
    tags=['Tenant']
)


# id = security.get_tenant_id
# Get tenant's company info
@router.get("/public_test", status_code=status.HTTP_200_OK)
def public_info():
    logger.info("Public test started")
    return {"msg": "test endpoint"}

@router.get("/get_client_info")
def get_client_info(request: Request):
    client_host = request.client.host
    client_origin = request.base_url
    logger.info(f"Client: {client_host}, origin: {client_origin}")
    return {"client_host" : client_host}

@router.get('/', status_code=status.HTTP_200_OK, response_model=general.StandardResponse[tenant.TenantResponse])
async def tenants(db: Session = Depends(get_db), current_tenants = Depends(deps.get_current_user)):
    logger.info("Tenant's info")
    company = await tenants_service.get_company_info(db, current_tenants)
    return general.StandardResponse(
        data=company,
        message="Tenant's info retrieved successfully",
    )

# Create a new tenant
@router.post('/add', status_code=status.HTTP_201_CREATED, response_model=general.StandardResponse[tenant.TenantResponse])
async def create_tenants(payload: tenant.TenantCreate, db: Session = Depends(get_base_db)):
    logger.info("Tenants created")
    tenant_obj = await tenants_service.create_tenant(db, payload)
    return general.StandardResponse(
        data=tenant_obj,
        message="Tenant created successfully"
    )

# Get all drivers for the current tenant
@router.get('/drivers', status_code=status.HTTP_200_OK, response_model=general.StandardResponse[list[driver.DriverResponse]])
async def get_drivers(db: Session = Depends(get_db), 
                      current_tenants = Depends(deps.get_current_user)):
    logger.info("Tenant drivers")
    drivers = await tenants_service.get_all_drivers(db, current_tenants)
    return general.StandardResponse(
        data=drivers,
        message="Drivers retrieved successfully",
        meta={"count": len(drivers)}
    )

# Get vehicles for the tenant, optionally filtered by driver or assignment
@router.get('/vehicles', status_code=status.HTTP_200_OK, response_model=general.StandardResponse[list[vehicle.VehicleResponse]])
async def get_vehicles(
    driver_id: Optional[int] = Query(None, description="Get vehicles for specific driver"),
    assigned_drivers: Optional[bool] = Query(False, description="Get only vehicles assigned to drivers"),
    db: Session = Depends(get_db),
    current_tenants = Depends(deps.get_current_user)
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
    return general.StandardResponse(
        data=vehicles,
        message="Drivers retrieved successfully",
        meta={"count": len(vehicles)}
    )

# Get bookings for the tenant, optionally filtered by status
@router.get('/bookings', status_code=status.HTTP_200_OK, response_model=general.StandardResponse[list[booking.BookingResponse]])
async def get_bookings(
    booking_status: Optional[str] = Query(None, description="only this labels can be passed 'pending', 'confirmed', 'active', 'cancelled', 'no_show'"),
    db: Session = Depends(get_db),
    current_tenant = Depends(deps.get_current_user)
):
    if booking_status:
        logger.info(f"Getting {booking_status} bookings...")
        bookings = await tenants_service.get_bookings_by_status(db, booking_status, current_tenant)
    else:
        logger.info(f"All available bookings for {current_tenant.id}")
        bookings = await tenants_service.get_all_bookings(db, current_tenant)
    return general.StandardResponse(
        data=bookings,
        message="Bookings retrieved successfully",
        meta={"count": len(bookings)}
    )

# Onboard a new driver for the tenant
@router.post('/onboard', status_code=status.HTTP_201_CREATED, response_model=general.StandardResponse[tenant.OnboardDriverResponse])
async def onboard_drivers(
    payload: tenant.OnboardDriver,
    db: Session = Depends(get_db),
    current_tenant = Depends(deps.get_current_user)
):
    logger.info("Onboarding driver...")
    new_driver = await tenants_service.onboard_drivers(db, payload, current_tenant)
    return general.StandardResponse(
        data=new_driver,
        message="New driver onboarded successfully"
    )

"""Assign driver to a booked rides pending drivers"""
@router.patch("/riders/{rider_id}/assign-driver", status_code=status.HTTP_202_ACCEPTED)
async def assign_driver_to_rides(payload: tenant.AssignDriver,
                        rider_id: int,db: Session = Depends(get_db),
                        current_tenant = Depends(deps.get_current_user)):
     
     assigned_driver = await tenants_service.assign_driver_to_rides(payload,rider_id,db, current_tenant)
     return assigned_driver

"""Assign drivers to vehicles"""
@router.patch("/vehicles/{vehicle_id}/assign-driver", status_code=status.HTTP_202_ACCEPTED)
async def assign_driver_to_vehicles(payload: tenant.AssignDriver,
                        vehicle_id: int,db: Session = Depends(get_db),
                        current_tenant = Depends(deps.get_current_user)):
     
     assigned_driver = await tenants_service.assign_driver_to_vehicle(payload,vehicle_id,db, current_tenant)
     return assigned_driver



###approve rides

# # Update tenant settings (future implementation)
# @router.patch('/settings', status_code=status.HTTP_202_ACCEPTED)
# async def update_settings(db: Session):
#     pass