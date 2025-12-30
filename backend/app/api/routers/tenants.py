from typing import Optional
from fastapi import APIRouter, HTTPException, FastAPI, Query, Response, status, Request, UploadFile, File, Form
from pydantic import EmailStr
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db, get_base_db
from ..core import deps
from ..services.booking_services import BookingService, get_booking_service
from ..services.tenants_service import TenantService, get_tenant_service, get_unauthorized_tenant_service
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
async def tenants(tenant_service: TenantService = Depends(get_tenant_service)):
    logger.info("Tenant's info")
    company = await tenant_service.get_company_info()
    return company

# Create a new tenant
@router.post('/add', status_code=status.HTTP_201_CREATED, response_model=general.StandardResponse[tenant.TenantRsponse])
    
async def create_tenants(   email: EmailStr = Form(...),
                            first_name: str = Form(..., min_length=1, max_length=200),
                            last_name: str = Form(..., min_length=1, max_length=200),
                            password: str = Form(min_length=8),
                            phone_no: str = Form(..., pattern = r'^\+?[\d\s\-\(\)]+$'),
                            company_name: str = Form(..., min_length=1, max_length=200),
                            # logo_url: Optional[UploadFile] = None
                            slug: str = Form(..., min_length=1, max_length=100, pattern=r'^[a-z0-9-]+$'),
                            address: Optional[str] = Form(None),
                            city: str = Form(..., min_length=1, max_length=100),
                            drivers_count: int = Form(default=0, ge=0),
                            logo_url: Optional[UploadFile] = File(None), 
                            tenant_service: TenantService = Depends(get_unauthorized_tenant_service),
                            db: Session = Depends(get_base_db)):
                            
        logger.info("Creating Tenant....")
        
        tenant_obj = await tenant_service.create_tenant(email=email,
                                                        first_name=first_name,
                                                        last_name=last_name,
                                                        password=password,
                                                        phone_no=phone_no,
                                                        company_name=company_name,
                                                        slug=slug,
                                                        address=address,
                                                        city=city,
                                                        drivers_count=drivers_count,
                                                        logo_url=logo_url, )
        return tenant_obj

# Get all drivers for the current tenant
@router.get('/drivers', status_code=status.HTTP_200_OK, response_model=general.StandardResponse[list[driver.DriverResponse]])
async def get_drivers(driver_id: Optional[int] = None,tenant_service: TenantService = Depends(get_tenant_service)):
    logger.info("Tenant drivers")
    drivers = await tenant_service.get_all_drivers(driver_id)
    return drivers

# DEPRECATED
@router.get('/vehicles', status_code=status.HTTP_200_OK, response_model=general.StandardResponse[list[vehicle.VehicleResponse]])
async def get_vehicles(
    driver_id: Optional[int] = Query(None, description="Get vehicles for specific driver"),
    assigned_drivers: Optional[bool] = Query(False, description="Get only vehicles assigned to drivers"),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    raise HTTPException(status_code=status.HTTP_410_GONE)
    if assigned_drivers:
        logger.info("Getting vehicles assigned to drivers")
        vehicles = await tenant_service.fetch_assigned_drivers_vehicles()
    elif driver_id:
        logger.info(f"Getting driver [{driver_id}] vehicles...")
        vehicles = await tenant_service.find_vehicles_owned_by_driver(driver_id)
    else:
        logger.info("Tenant vehicles...")
        vehicles = await tenant_service.get_all_vehicles()
    return vehicles

# Get bookings for the tenant, optionally filtered by status
@router.get('/bookings', status_code=status.HTTP_200_OK, response_model=general.StandardResponse[list[booking.BookingPublic]])
async def get_bookings(
    booking_id: Optional[str] = None,
    booking_status: Optional[str] = Query(None, description="only this labels can be passed 'pending', 'confirmed', 'active', 'cancelled', 'no_show'"),service_type: Optional[booking.ServiceType] =None, vehicle_id: Optional[int] =None,limit: Optional[int] =None, 
    booking_service: BookingService = Depends(get_booking_service)
):
    logger.debug("I am hittting tenant for bookings ")
    bookings = await booking_service.get_bookings_by(booking_id=booking_id, booking_status=booking_status, service_type=service_type, vehicle_id=vehicle_id, limit=limit)
        
    return bookings

# Onboard a new driver for the tenant
@router.post('/onboard', status_code=status.HTTP_201_CREATED, response_model=general.StandardResponse[tenant.OnboardDriverResponse])
async def onboard_drivers(
    payload: tenant.OnboardDriver,
    tenant_service: TenantService = Depends(get_tenant_service)
):
    logger.info("Onboarding driver...")
    new_driver = await tenant_service.onboard_drivers(payload)
    return new_driver

"""Assign driver to a booked rides pending drivers"""
@router.patch("/bookings/{booking_id}/assign-driver", status_code=status.HTTP_202_ACCEPTED)
async def assign_driver_to_rides(payload: tenant.AssignDriver,
                                booking_id: int,
                                tenant_service: TenantService = Depends(get_tenant_service)):
     
     assigned_driver = await tenant_service.assign_driver_to_rides(payload, booking_id)
     return assigned_driver

"""Assign drivers to vehicles"""
@router.patch("/vehicles/{vehicle_id}/assign/{driver_id}", status_code=status.HTTP_202_ACCEPTED)
async def assign_driver_to_vehicles(driver_id:int, vehicle_id: int,
                        tenant_service: TenantService = Depends(get_tenant_service)):
     
     assigned_driver = await tenant_service.assign_driver_to_vehicle(driver_id, vehicle_id)
     return assigned_driver

@router.patch("/vehicles/{vehicle_id}/unassign/driver", status_code=status.HTTP_202_ACCEPTED)
async def unassign_driver_from_vehicle(vehicle_id: int,override:bool = False,
                        
                        tenant_service: TenantService = Depends(get_tenant_service)):
     
     assigned_driver = await tenant_service.unassign_driver_from_vehicles(override=override, vehicle_id=vehicle_id)
     return assigned_driver

###approve rides

# # Update tenant settings (future implementation)
# @router.patch('/settings', status_code=status.HTTP_202_ACCEPTED)
# async def update_settings(db: Session):
#     pass