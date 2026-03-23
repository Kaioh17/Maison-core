from fastapi import APIRouter, HTTPException, FastAPI, Response, status, Query, Path
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db, get_base_db
# from ..services import driver_service
from app.schemas import driver, booking, general
from ..core import deps
from .dependencies import is_driver, api_key_header, API_KEY, verify_api_key
from typing import Optional
from app.utils.logging import logger
from ..services.driver_service import DriverService,RiderDriverService,get_driver_service, get_unauthorized_driver_service, get_rdriver_service
from ..services.booking_services import get_booking_service, BookingService
"""

TODO drivers endpoint: 

Driver activity toggle (api/v1/driver/active?is_active=true/false)
Accept ride button refine endpoint 
UPDATE vehicle information (patch api/v1/driver/) 
"""

router = APIRouter(
    prefix="/api/v1/driver",
    tags=["Drivers"],
)


@router.patch(
    "/status",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=general.StandardResponse[dict],
    summary="Toggle driver active status",
    description="Enable or disable the authenticated driver account (`is_active`). Requires driver JWT.",
    response_description="Standard success payload with updated status info.",
)
async def driver_status(
    is_active: bool,
    is_driver: bool = Depends(is_driver),
    driver_service: DriverService = Depends(get_driver_service),
):
    status = await driver_service.driver_status(is_active=is_active)
    return status


@router.get(
    "/{slug}/verify",
    status_code=status.HTTP_200_OK,
    response_model=general.StandardResponse[dict],
    dependencies=[Depends(verify_api_key)],
    summary="Verify driver onboarding token (API key)",
    description=(
        "Public pre-login step: validate **`token`** for the tenant **`slug`** (invitation / onboarding link). "
        "Requires **`X-API-Key`** header matching server config."
    ),
    response_description="Token validation result for registration flow.",
)
async def verify_driver_token(
    slug: str = Path(..., description="Tenant slug from onboarding link."),
    token: str = Query(..., description="Driver onboarding token."),
    driver_service: DriverService = Depends(get_unauthorized_driver_service),
):
    logger.info("Driver..")
    token = await driver_service.check_token(slug=slug, token=token)
    return token


@router.patch(
    "/register",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=general.StandardResponse[driver.DriverResponse],
    summary="Complete driver registration",
    description=(
        "Submit driver profile after invite; associates the driver with **`tenant_id`**. "
        "Typically used after `/driver/{slug}/verify`. No driver JWT required (unauthorized service)."
    ),
    response_description="Created driver record.",
)
async def register_driver(
    tenant_id: int = Query(..., description="Tenant id this driver belongs to."),
    payload: driver.DriverCreate = ...,
    driver_service: DriverService = Depends(get_unauthorized_driver_service),
    db: Session = Depends(get_base_db),
):
    logger.info("Registration begins....")
    driver = await driver_service.register_driver(payload, tenant_id=tenant_id)
    return general.StandardResponse(
        data=driver,
        message="Driver registered successfully",
    )


@router.get(
    "/info",
    status_code=status.HTTP_200_OK,
    response_model=general.StandardResponse[driver.DriverResponse],
    summary="Get current driver profile",
    description="Returns the authenticated driver's profile. Requires driver JWT.",
    response_description="Driver profile.",
)
async def get_driver_info(
    is_driver: bool = Depends(is_driver),
    driver_service: DriverService = Depends(get_driver_service),
):
    logger.info("Driver..")
    driver = await driver_service.get_driver()
    return general.StandardResponse(
        data=driver,
        message="Driver info recieved successfully",
    )


@router.get(
    "/rider/info",
    status_code=status.HTTP_200_OK,
    response_model=general.StandardResponse[list[driver.RiderDriverResponse]],
    summary="Rider view: limited driver info",
    description="Riders can fetch sanitized driver details (e.g. for a booking). Optional **`driver_id`** filter.",
    response_description="List of driver public fields.",
)
async def get_driver_info_for_rider(
    driver_id: int = None,
    driver_service: RiderDriverService = Depends(get_rdriver_service),
    current_driver: int = Depends(deps.get_current_user),
):
    logger.info("Rider..")
    driver = await driver_service.get_driver_info(driver_id=driver_id)
    return driver


@router.get(
    "/rides/available",
    status_code=status.HTTP_200_OK,
    response_model=general.StandardResponse[list[booking.BookingPublic]],
    summary="[Deprecated] List available rides",
    description="**410 Gone** — replaced by other booking listing flows.",
    response_description="Not used.",
)
async def get_bookings_for_driver_deprecated(
    is_driver: bool = Depends(is_driver),
    booking_status: Optional[str] = None,
    booking_servcie: BookingService = Depends(get_booking_service),
):
    logger.info("Availble rides")
    raise HTTPException(
        status_code=status.HTTP_410_GONE, detail="Endpoint deprecated"
    )


from ..services.analytics.driver import get_driver_analytics, DriverAnalyticService


@router.get(
    "/booking/analytics",
    status_code=status.HTTP_200_OK,
    response_model=general.StandardResponse[booking.BookingAnalyticsresponse],
    summary="Driver booking analytics",
    description="Aggregated booking stats for the authenticated driver (counts by status, etc.).",
    response_description="Analytics payload.",
)
async def get_driver_booking_analytics(
    is_driver: bool = Depends(is_driver),
    booking_status: Optional[str] = None,
    booking_servcie: DriverAnalyticService = Depends(get_driver_analytics),
):
    bookings = await booking_servcie.booking_analytics()
    return bookings


@router.get(
    "/upcoming/rides",
    status_code=status.HTTP_200_OK,
    response_model=general.StandardResponse[list[booking.BookingPublic]],
    summary="List upcoming rides for driver",
    description="Bookings assigned to this driver that are upcoming / in progress.",
    response_description="List of bookings.",
)
async def get_upcoming_rides(
    is_driver: bool = Depends(is_driver),
    booking_servcie: BookingService = Depends(get_booking_service),
):
    logger.info("Availble rides")
    bookings = await booking_servcie.get_upcoming_rides()
    return bookings


@router.patch(
    "/ride/{booking_id}/decision",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=general.StandardResponse[dict],
    summary="Accept or decline a booking",
    description=(
        "Driver responds to a pending ride request. **`action`** query describes the decision (e.g. confirm/cancel flow); "
        "**`approve_action`** refines behavior per service implementation."
    ),
    response_description="Result of the ride decision.",
)
async def set_ride_status(
    booking_id: int = Path(..., description="Booking id."),
    action: str = Query(
        None, description="Decision label (e.g. Confirm / Cancelled) — see service."
    ),
    approve_action: bool = False,
    is_driver: bool = Depends(is_driver),
    driver_service: DriverService = Depends(get_driver_service),
):
    ride_decision = await driver_service.driver_ride_response(
        action, booking_id, approve_action=approve_action
    )
    return ride_decision