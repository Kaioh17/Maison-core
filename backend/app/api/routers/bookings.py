from typing import Optional
from fastapi import APIRouter, status, Path
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from ..services.booking_services import (
    get_booking_service,
    BookingService,
)
from app.schemas import booking
from app.schemas.general import StandardResponse
from ..core import deps
from .dependencies import is_rider
from app.utils.logging import logger
from ..services.stripe_services.checkout import BookingCheckout, get_checkout_service


router = APIRouter(
    prefix="/api/v1/bookings",
    tags=["Bookings"],
)


@router.get(
    "/public_test",
    status_code=status.HTTP_200_OK,
    summary="Health / connectivity test",
    description="Unauthenticated smoke test.",
    response_description="Static JSON message.",
)
def public_info():
    logger.info("Public test started")
    return {"msg": "test endpoint"}


@router.post(
    "/set",
    status_code=status.HTTP_201_CREATED,
    response_model=StandardResponse[booking.BookingPublic],
    summary="Create a booking (rider)",
    description=(
        "Creates a ride request (airport, hourly, dropoff, etc.). "
        "Requires **rider** JWT; pricing and routing run in the booking service."
    ),
    response_description="Created booking with estimates.",
)
async def book_ride(
    book_ride: booking.CreateBooking,
    booking_service: BookingService = Depends(get_booking_service),
    current_rider=Depends(deps.get_current_user),
    db: Session = Depends(get_db),
    rider=Depends(is_rider),
):
    ride_booked = await booking_service.book_ride(book_ride)
    return ride_booked


@router.patch(
    "/{booking_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=StandardResponse[dict],
    summary="Confirm or update booking payment step",
    description=(
        "Rider confirms a quote / proceeds with payment metadata (`Payment` schema). "
        "Requires **rider** JWT."
    ),
    response_description="Updated booking / payment state.",
)
async def approve_ride(
    booking_id: int = Path(..., description="Booking id."),
    payload: booking.Payment = ...,
    booking_service: BookingService = Depends(get_booking_service),
    is_rider=Depends(is_rider),
):
    ride_approved = await booking_service.confirm_ride(
        booking_id=booking_id, payload=payload
    )
    return ride_approved


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[list[booking.BookingPublic]],
    summary="List bookings for current user",
    description=(
        "Returns bookings for the authenticated user (role-aware in service). "
        "Optional filters: **`booking_id`**, **`booking_status`**, **`limit`**, **`service_type`**, **`vehicle_id`**."
    ),
    response_description="List of bookings.",
)
async def list_bookings(
    booking_id: Optional[int] = None,
    booking_status: Optional[str] = None,
    limit: Optional[int] = None,
    service_type: Optional[str] = None,
    vehicle_id: Optional[int] = None,
    booking_service: BookingService = Depends(get_booking_service),
):
    booked_rides = await booking_service.get_bookings_by(
        booking_id=booking_id,
        booking_status=booking_status,
        limit=limit,
        service_type=service_type,
        vehicle_id=vehicle_id,
    )
    return booked_rides


@router.post(
    "/stripe/{booking_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=StandardResponse[dict],
    summary="Create Stripe Checkout session for a booking",
    description=(
        "Creates a hosted Checkout session to pay deposit or balance for **`booking_id`**. "
        "Requires **rider** JWT. (Path was corrected to `/stripe/{booking_id}`.)"
    ),
    response_description="Checkout session id / URL payload.",
)
async def booking_checkout_session(
    booking_id: int = Path(..., description="Booking to pay for."),
    checkout_service: BookingCheckout = Depends(get_checkout_service),
    is_rider=Depends(is_rider),
):
    ride_booked = await checkout_service.checkout_session(booking_id=booking_id)
    return ride_booked
