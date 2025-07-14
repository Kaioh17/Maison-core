from fastapi import HTTPException, status
from app.models import booking, tenant, driver
from app.utils import password_utils
from app.utils.logging import logger
from datetime import timedelta, datetime

role_to_booking_field  = {
    "driver": booking.Bookings.driver_id,
    "rider": booking.Bookings.rider_id,
    "tenant": booking.Bookings.tenant_id,
}
# user_table = user.Users
tenant_table = tenant.Tenants
driver_table = driver.Drivers
booking_table = booking.Bookings

def _bookings_overlap(db, payload):
     #check for overlaps

    #
    exists = db.query(booking_table).filter(booking_table.vehicle_id == payload.vehicle_id).all()
    
    if not exists: return

    new_start =  payload.pickup_time
    new_end =  payload.dropoff_time

    for booking in exists:
    
        start_time = booking.pickup_time
        end_time = booking.dropoff_time + timedelta(minutes=15)

        if new_start >= new_end:
            logger.warning(f"strat time {new_start} is greater than end time {new_end}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail = "conflict: start time cannot be higher that end time")

        if (start_time <= new_start <= end_time
            or start_time <= new_end <= end_time
                or (payload.pickup_time <= start_time and payload.dropoff_time>= end_time) ):
            logger.warning(f"Time slot overlap with {booking.id}")
            
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail = "Time slot overlap with existing booking")



async def book_ride(payload, db, current_rider):
    book_ride_info = payload.model_dump()
    new_ride = booking.Bookings(rider_id = current_rider.id,tenant_id = current_rider.tenant_id,**book_ride_info)

    
    tenant_query = db.query(tenant.Tenants).filter(tenant.Tenants.id == current_rider.tenant_id).first()
    driver_query = db.query(driver.Drivers).filter(driver.Drivers.id == payload.driver_id).first()

    if not tenant_query: 
        raise HTTPException(status_code=404, detail="tenant not found")
    if not driver_query: 
        raise HTTPException(status_code=404, detail="driver not found")
    

    #check for overlaps
    _bookings_overlap(db, payload)

    

    db.add(new_ride)
    db.commit()
    db.refresh(new_ride)

    logger.info(f"A new ride has been set for {current_rider.full_name}")

    return new_ride


async def get_booked_rides(db, current_user):
    user = current_user.role
    rows = role_to_booking_field .get(user.lower())

    if not rows:
        raise ValueError("Role not in settings")

    booked_rides = db.query(booking.Bookings).filter(rows == current_user.id).all()

    if not booked_rides:
        raise HTTPException(status_code=404, detail = "There are no scheduled rides available")

    return booked_rides

