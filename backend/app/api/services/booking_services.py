from fastapi import HTTPException, status
from app.models import booking, tenant, driver, vehicle_config, vehicle
from app.utils import db_error_handler
from app.utils.logging import logger
from datetime import timedelta, datetime
from sqlalchemy.exc import *

from app.models import tenant_setting

db_exceptions = db_error_handler.DBErrorHandler

role_to_booking_field  = {
    "driver": booking.Bookings.driver_id,
    "rider": booking.Bookings.rider_id,
    "tenant": booking.Bookings.tenant_id,
}
# user_table = user.Users
tenant_table = tenant.Tenants
driver_table = driver.Drivers
booking_table = booking.Bookings
tenant_setting_table = tenant_setting.TenantSettings  
vehicle_config_table = vehicle_config.VehicleConfig
vehicle_table = vehicle.Vehicles

def _bookings_overlap(db, payload):
     #check for overlaps
    try:
        exists = db.query(booking_table).filter(booking_table.vehicle_id == payload.vehicle_id).all()
        """If we implement driver model:
                cases:
                    if drivers are outsourced or contracted:
                        we will have to check if both the driver and that vehicle are available
                    elif drivers are inhouse:
                        we will check if the vehicle is available and if that 
        """

        logger.info(f"Checking for any booking overlaps")

        if not exists: 
            logger.info(f"There are no overlaps")

            return

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
    except db_exceptions.COMMON_DB_ERRORS as e:
        db_exceptions.handle(e, db)



async def book_ride(payload, db, current_rider):

    try:
        price_estimate = await _price_quote(db, current_rider, payload)
        book_ride_info = payload.model_dump()
        vehicle = db.query(vehicle_table).filter_by(id=payload.vehicle_id).first()
        if not vehicle:
            raise HTTPException(status_code=404, detail="vehicle not found")

        new_ride = booking.Bookings(rider_id = current_rider.id,tenant_id = current_rider.tenant_id,
                                    estimated_price = price_estimate,driver_id = vehicle.driver_id,**book_ride_info)

       
        if not db.query(tenant.Tenants).filter(tenant.Tenants.id == current_rider.tenant_id).first(): 
            raise HTTPException(status_code=404, detail="tenant not found")
      
        
        if not payload.city:
            logger.warning(f"City was not entered for rider {current_rider.id}")
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                                detail= "City was not entered..")

        #check for overlaps
        _bookings_overlap(db, payload)

        

        db.add(new_ride)
        db.commit()
        db.refresh(new_ride)

        logger.info(f"A new ride has been set for {current_rider.full_name}")
        return new_ride

    except db_exceptions.COMMON_DB_ERRORS as e:
        db_exceptions.handle(e, db)
      
   

async def get_booked_rides(db, current_user):
    try:
        user = current_user.role
        rows = role_to_booking_field.get(user.lower())

        if not rows:
            raise ValueError("Role not in settings")

        booked_rides = db.query(booking.Bookings).filter(rows == current_user.id).all()

        if not booked_rides:
            raise HTTPException(status_code=404, detail = "There are no scheduled rides available")

        return booked_rides
    except db_exceptions.COMMON_DB_ERRORS as e:
        db_exceptions.handle(e, db)

async def _price_quote(db, current_user, payload):
    try: 
        settings = db.query(tenant_setting_table).filter(tenant_setting_table.tenant_id == current_user.tenant_id).first()
        vehicle_base_price = db.query(vehicle_config_table).filter(vehicle_config_table.vehicle_id == payload.vehicle_id).first()
        if not settings:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail= "Settingd for tenants found...")
        #calculate price
        logger.info(f"base_fare = {settings.base_fare}")
        base_fare = settings.base_fare
        per_mile_rate = settings.per_mile_rate
        
        per_minute_rate = settings.per_minute_rate
        vehicle_rate = vehicle_base_price.vehicle_flat_rate
       
        total_quote = base_fare + per_mile_rate + per_minute_rate + vehicle_rate 

        if payload.service_type.lower() == "hourly":
            per_hour_rate = settings.per_hour_rate
            total_quote = total_quote + per_hour_rate

        return total_quote
    except db_exceptions.COMMON_DB_ERRORS as e:
        db_exceptions.handle(e, db)