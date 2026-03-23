from typing import Optional
from fastapi import APIRouter, HTTPException, FastAPI, Query, Response, status, Request, UploadFile, File, Form
from pydantic import EmailStr
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db, get_base_db
from ..core import deps
from ..services.booking_services import BookingService, get_booking_service
from ..services.tenants_service import TenantService, get_tenant_service, get_unauthorized_tenant_service
from ..services.analytics.tenant import TenantAnalyticService, get_tenant_analytics
from app.schemas import tenant, driver, vehicle, booking, general
from ..core import security, deps
from app.utils.logging import logger


# from .dependencies import get_tenant_id_from_token 

router = APIRouter(
    prefix="/api/v1/tenant",
    tags=["Tenant"],
)


@router.get(
    "/public_test",
    status_code=status.HTTP_200_OK,
    summary="Health / connectivity test",
    description="Unauthenticated smoke test returning a static message.",
    response_description="Simple JSON message.",
)
def public_info():
    logger.info("Public test started")
    return {"msg": "test endpoint"}


@router.get(
    "/get_client_info",
    summary="Debug: client host",
    description="Returns the connecting client's host and base URL (debugging / proxies).",
    response_description="`client_host` and related info.",
    deprecated=True
)
def get_client_info(request: Request):
    client_host = request.client.host
    client_origin = request.base_url
    logger.info(f"Client: {client_host}, origin: {client_origin}")
    return {"client_host": client_host}


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=general.StandardResponse[tenant.TenantResponse],
    summary="Get current tenant company profile",
    description="Returns the authenticated tenant's company info and related profile fields. Requires **tenant** JWT.",
    response_description="Tenant profile payload.",
)
async def get_tenant_company_info(
    tenant_service: TenantService = Depends(get_tenant_service),
):
    logger.info("Tenant's info")
    company = await tenant_service.get_company_info()
    return company


@router.post(
    "/add",
    status_code=status.HTTP_201_CREATED,
    response_model=general.StandardResponse[tenant.TenantRsponse],
    summary="Register a new tenant (company)",
    description=(
        "Public signup: creates tenant account, company profile, default settings/pricing, optional logo upload. "
        "Multipart form; **`slug`** must be URL-safe (lowercase, hyphens)."
    ),
    response_description="Created tenant + profile.",
)
async def create_tenants(
    email: EmailStr = Form(...),
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


@router.get(
    "/drivers",
    status_code=status.HTTP_200_OK,
    response_model=general.StandardResponse[list[driver.DriverResponse]],
    summary="List drivers for this tenant",
    description="Optional **`driver_id`** to fetch a single driver. Requires **tenant** JWT.",
    response_description="List of drivers.",
)
async def get_tenant_drivers(
    driver_id: Optional[int] = None,
    tenant_service: TenantService = Depends(get_tenant_service),
):
    logger.info("Tenant drivers")
    drivers = await tenant_service.get_all_drivers(driver_id)
    return drivers


@router.get(
    "/vehicles",
    status_code=status.HTTP_200_OK,
    response_model=general.StandardResponse[list[vehicle.VehicleResponse]],
    summary="[Deprecated] List vehicles",
    description="**410 Gone** — use `/api/v1/vehicles` instead.",
    response_description="Not used.",
)
async def get_vehicles_deprecated(
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


@router.get(
    "/bookings",
    status_code=status.HTTP_200_OK,
    response_model=general.StandardResponse[list[booking.BookingPublic]],
    summary="List bookings for this tenant",
    description=(
        "Filter by **`booking_status`**, **`service_type`**, **`vehicle_id`**, **`booking_id`**, or **`limit`**. "
        "Requires **tenant** JWT; results scoped to tenant."
    ),
    response_description="List of bookings.",
)
async def get_tenant_bookings(
    booking_id: Optional[str] = None,
    booking_status: Optional[str] = Query(None, description="only this labels can be passed 'pending', 'confirmed', 'active', 'cancelled', 'no_show'"),service_type: Optional[str] =None, vehicle_id: Optional[int] =None,limit: Optional[int] =None, 
    booking_service: BookingService = Depends(get_booking_service)
):
    logger.debug("I am hittting tenant for bookings ")
    bookings = await booking_service.get_bookings_by(booking_id=booking_id, booking_status=booking_status, service_type=service_type, vehicle_id=vehicle_id, limit=limit)
        
    return bookings


@router.post(
    "/onboard",
    status_code=status.HTTP_201_CREATED,
    response_model=general.StandardResponse[tenant.OnboardDriverResponse],
    summary="Invite / onboard a driver",
    description="Creates driver invite + onboarding token and notification flow. Requires **tenant** JWT.",
    response_description="Onboarding result (e.g. token, email status).",
)
async def onboard_drivers(
    payload: tenant.OnboardDriver,
    tenant_service: TenantService = Depends(get_tenant_service)
):
    logger.info("Onboarding driver...")
    new_driver = await tenant_service.onboard_drivers(payload)
    return new_driver


@router.patch(
    "/bookings/{booking_id}/assign-driver",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Assign a driver to a booking",
    description="Maps a **`driver_id`** to a pending booking. Requires **tenant** JWT.",
    response_description="Assignment result.",
)
async def assign_driver_to_rides(
    payload: tenant.AssignDriver,
    booking_id: int,
    tenant_service: TenantService = Depends(get_tenant_service),
):
    assigned_driver = await tenant_service.assign_driver_to_rides(payload, booking_id)
    return assigned_driver


@router.patch(
    "/vehicles/{vehicle_id}/assign/{driver_id}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Assign a driver to a vehicle",
    description="Links fleet vehicle to driver (one-to-one style per business rules). Requires **tenant** JWT.",
    response_description="Updated vehicle/driver association.",
)
async def assign_driver_to_vehicles(
    driver_id: int,
    vehicle_id: int,
    tenant_service: TenantService = Depends(get_tenant_service),
):
    assigned_driver = await tenant_service.assign_driver_to_vehicle(driver_id, vehicle_id)
    return assigned_driver


@router.patch(
    "/vehicles/{vehicle_id}/unassign/driver",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Unassign driver from a vehicle",
    description="Clears driver assignment on a vehicle; **`override`** may allow forced reassignment. Requires **tenant** JWT.",
    response_description="Unassignment result.",
)
async def unassign_driver_from_vehicle(
    vehicle_id: int,
    override: bool = False,
    tenant_service: TenantService = Depends(get_tenant_service),
):
    assigned_driver = await tenant_service.unassign_driver_from_vehicles(
        override=override, vehicle_id=vehicle_id
    )
    return assigned_driver


@router.post(
    "/stripe",
    status_code=status.HTTP_201_CREATED,
    response_model=general.StandardResponse[dict],
    summary="Create Stripe Connect Express account",
    description="Starts Express onboarding for the tenant to receive payouts. Requires **tenant** JWT.",
    response_description="Stripe account ids / onboarding payload.",
)
async def setup_stripe_express_account(
    tenant_service: TenantService = Depends(get_tenant_service),
):
    setup_account = tenant_service.stripe_account_setup()
    return setup_account


from ..services.stripe_services.stripe_service import StripeService, get_stripe_service


@router.get(
    "/stripe/link",
    status_code=status.HTTP_200_OK,
    response_model=general.StandardResponse[dict],
    summary="Get Stripe Express onboarding / login link",
    description="Returns an Account Link for Connect onboarding or dashboard login. Requires **tenant** JWT.",
    response_description="URL payload for redirecting the user to Stripe.",
)
async def get_stripe_account_link(
    stripe_service: StripeService = Depends(get_stripe_service),
):
    login_link = stripe_service.get_account_link()
    return login_link


@router.get(
    "/analysis",
    status_code=status.HTTP_200_OK,
    response_model=general.StandardResponse[tenant.BookingAnalyticsData],
    summary="Tenant dashboard analytics",
    description="Aggregated KPIs: rides, revenue, fleet counts, etc. Requires **tenant** JWT.",
    response_description="Analytics object.",
)
async def get_tenant_analytics(
    tenant_service: TenantAnalyticService = Depends(get_tenant_analytics),
):
    analytics = await tenant_service.analytics()
    return analytics


@router.post(
    "/driver",
    status_code=status.HTTP_201_CREATED,
    summary="Convert tenant user to driver (optional flow)",
    description="Internal flow to create a driver profile for the current tenant user. Requires **tenant** JWT.",
    response_description="Result of driver conversion.",
)
async def become_driver(
    request: Request, tenant_service: TenantService = Depends(get_tenant_service)
):
    be_driver = await tenant_service.be_driver(request=request)
    return be_driver


@router.get(
    "/is_driver",
    status_code=status.HTTP_200_OK,
    response_model=general.StandardResponse[dict],
    summary="Check if tenant also has a driver profile",
    description="Returns whether this tenant account is linked to a driver record. Requires **tenant** JWT.",
    response_description="Boolean / status payload.",
)
async def get_driver_status_for_tenant(
    tenant_service: TenantService = Depends(get_tenant_service),
):
    analytics = await tenant_service.is_driver()
    return analytics