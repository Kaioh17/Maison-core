import asyncio
import math
import time
from zoneinfo import ZoneInfo
from fastapi import HTTPException, status, Depends
from app.db.database import get_db
from ..core import deps
from app.models import *
from app.utils import db_error_handler
from app.utils.logging import logger
from datetime import timedelta, datetime
from sqlalchemy.exc import *
from app.schemas.booking import BookingResponse
from .helper_service import success_resp, success_list_resp
from .service_context import ServiceContext
from .email_services import drivers, tenants, riders
from .helper_service import (
    user_table,
    tenant_table,
    tenant_profile,
    tenant_stats,
    tenant_branding,
    tenant_pricing,
    driver_table,
    booking_table,
    
    tenant_setting_table,
    vehicle_config_table,
    vehicle_category_table,
    vehicle_table
)

from app.models import tenant_setting
db_exceptions = db_error_handler.DBErrorHandler

class BookingService(ServiceContext):
    def __init__(self, db, current_user):
        
        super().__init__(db, current_user)
            
    db_exceptions = db_error_handler.DBErrorHandler
            
    role_to_booking_field  = {
        "driver": booking.Bookings.driver_id,
        "rider": booking.Bookings.rider_id,
        "tenant": booking.Bookings.tenant_id,
        }
    def _distance_in_miles(self,coordinate):
        # based on distance 
        ## d prefix -> dropoff_location and p prefix -> pickup_location
        dlon = coordinate.dlon
        dlat = coordinate.dlat
        plat = coordinate.plat
        plon = coordinate.plon
        
        logger.debug(f'Coordinates: {coordinate}')
        lon1 = math.radians(dlon)
        lon2 = math.radians(plon)
        lat1 = math.radians(dlat)
        lat2 = math.radians(plat)
        
        #differences
        lat_diff = lat2 - lat1
        lon_diff = lon2 - lon1
        
        #haversine formula
        a = math.sin(lat_diff / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(lon_diff / 2)**2
        c = 2 * math.asin(math.sqrt(a))

        
        R = 3958.8 #earth radius in miles
        distance = R*c
        logger.info(f"latdiffernce{lat_diff} and londiffernce{lon_diff}---->c = {c} distance {distance}")
        return distance ##returns total distance in miles
    async def _eta(self, distance, booking_obj:object):
        try:
            logger.debug(f"{booking_obj.service_type}")
            if booking_obj.service_type != "hourly":
                
                logger.debug(f"{distance}")
                
                duration = (distance/45) * 3600
                start_time = booking_obj.pickup_time
                det_est_time =  start_time + timedelta(seconds=duration)
                # booking_obj.dropoff_time = 
                return det_est_time
            else:
                return start_time + timedelta(hours=booking_obj.hours)
             
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)
    def _to_user_time_zone(self, dt_utc: datetime, user_tz: str = "America/Chicago"):
        if type(dt_utc) == str:
            dt_utc = datetime.fromisoformat(dt_utc)
        # logger.debug(f"datetime:{dt_utc} as {type(dt_utc)}")
        tz = dt_utc.astimezone(ZoneInfo(user_tz))
        # logger.debug(f"User timezone {tz} for {user_tz}")
        return tz
    def _to_local_time(self, data):
        try:
            logger.debug(f"data type: {type(data)}")
            
            if type(data) == dict:
                for k, v in data.items():
                    if k == "dropoff_time" or k == "pickup_time":
                        logger.debug(f"Checked time found {v}")
                        data[k] = self._to_user_time_zone(dt_utc = v)
                        logger.debug("transformed time")
                        
            elif type(data) == list:
                for dict_ in data:
                    # logger.debug(dict_)
                    for k, v in dict_.items():
                        if k == "dropoff_time" or k == "pickup_time":
                            dict_[k] = self._to_user_time_zone(dt_utc = v)
            
            return data
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)
    async def confirm_ride(self, booking_id: int, payload):
        try:
            is_approved = payload.is_approved
            if is_approved:
                response:booking_table = self.db.query(booking_table).filter(booking_table.tenant_id == self.tenant_id, booking_table.id == booking_id).first()
                if not response:
                    logger.debug("Booking_id cannot be found.")
                    raise HTTPException(status_code=404,detail="Booking_id cannot be found.")
                response.is_approved = is_approved
                response.payment_method = payload.payment_method
                self.db.commit()
                #send email
                
                if response.driver_id:
                    driver_ = await self._get_driver_fullname(driver_id = response.driver_id)
                    driver_full_name = driver_.full_name
                    driver_email = driver_.email
                    ##email
                    # tenants.TenantEmailServices(to_email=self.tenant_email, from_email=self.tenant_email).new_ride(booking)
                    # drivers.DriverEmailServices(to_email=driver_email, from_email=self.tenant_email).new_ride(booking_obj=new_ride, assigned=False)
                    drivers.DriverEmailServices(to_email=driver_email, from_email=self.tenant_email).new_ride(booking_obj=response, assigned=False, slug=self.slug)
                else:
                    driver_full_name = "No driver assigned"
                
                # Email: Send booking confirmation to rider
                rider_obj = self.db.query(user_table).filter(user_table.id == self.current_user.id).first()
                vehicle_info = f"{response.vehicle.vehicle_name}"
                logger.debug(f"{vehicle_info}")
                await riders.RiderEmailServices(to_email=self.current_user.email, from_email=self.tenant_email).booking_confirmation_email(
                    booking_obj=response,
                    rider_obj=rider_obj,
                    slug=self.slug,
                    vehicle_info=vehicle_info,
                    driver_name=driver_full_name if response.vehicle.driver_id else None
                )
                await asyncio.sleep(3)
                # Email: Send new booking notification to tenant
                tenant_obj = self.db.query(tenant_table).filter(tenant_table.id == self.current_user.tenant_id).first()
                await tenants.TenantEmailServices(to_email=self.tenant_email, from_email=self.tenant_email).booking_notification_email(
                    booking_obj=response,
                    tenant_obj=tenant_obj,
                    slug=self.slug,
                    rider_name=self.full_name,
                    vehicle_info=vehicle_info
                )
                
                logger.info(f"A new ride has been set for {self.current_user.full_name}")
                return success_resp(msg="Ride was approved", data={"is_approved": is_approved})
            
            else:
                #sendemail
                return success_resp(msg="Ride was not approved", data={"is_approved": is_approved})
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)
    async def book_ride(self, payload):
        """Rider books a ride"""
        try:
            
            book_ride_info = payload.model_dump(exclude="coordinates")
            logger.debug(f"{book_ride_info}")
            
            vehicle = self.db.query(vehicle_table).filter_by(id=payload.vehicle_id).first()
            if not vehicle:
                raise HTTPException(status_code=404, detail="vehicle not found")
            
            ##
            distance = self._distance_in_miles(payload.coordinates)
            eta = await self._eta(distance=distance, booking_obj=payload)
                
            price_estimate = await self._price_quote(payload, distance=distance)
            book_ride_info['dropoff_time'] = eta
            payload.dropoff_time = eta
            
            logger.debug(f"Eta {eta} payload {payload.dropoff_time}price {price_estimate} data {book_ride_info}")
            new_ride = booking.Bookings(rider_id = self.current_user.id,tenant_id = self.current_user.tenant_id,
                                        estimated_price = price_estimate,driver_id = vehicle.driver_id,**book_ride_info)

            
            if not self.db.query(tenant.Tenants).filter(tenant.Tenants.id == self.current_user.tenant_id).first(): 
                raise HTTPException(status_code=404, detail="tenant not found")
        
            
            if not payload.country:
                logger.warning(f"Country was not entered for rider {self.current_user.id}")
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                                    detail= "Country was not entered..")

            #check for overlaps
            self._bookings_overlap( payload)            
            
            self.db.add(new_ride)
        
            self.db.commit()
            self.db.refresh(new_ride)
            
            # new_data = new_ride
            new_data = self._to_local_time(new_ride.__dict__)
            logger.debug(f"new_data {new_data['dropoff_time']} old data {new_ride.dropoff_time}")
            
            if new_ride.driver_id:
                    driver_ = await self._get_driver_fullname(driver_id = new_ride.driver_id)
                    driver_full_name = driver_.full_name
                    # driver_email = driver_.email
                    ##email
                    # tenants.TenantEmailServices(to_email=self.tenant_email, from_email=self.tenant_email).new_ride(booking)
                    # drivers.DriverEmailServices(to_email=driver_email, from_email=self.tenant_email).new_ride(booking_obj=new_ride, assigned=False)
                    # drivers.DriverEmailServices(to_email=driver_email, from_email=self.tenant_email).new_ride(booking_obj=new_ride, assigned=False, slug=self.slug)
            else:
                driver_full_name = "No driver assigned"
            
            
            return success_resp(msg="Booking Successfull", data= {"driver_name":driver_full_name ,"customer_name": self.full_name,"vehicle": f"{vehicle.make} {vehicle.model} {vehicle.year}",**new_data})
        
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)
            
      
            
    async def get_bookings_by(self,booking_id = None ,booking_status: str = None,
                              service_type: str =None,vehicle_id: int =None, limit: int = None ):
        try:
            limit_per_user = {"rider": 5, "tenant": 25, "driver":5}
            limit = limit_per_user[self.role.lower()] if limit == None else limit
            execute_params ={"booking_status":booking_status, "tenant_id":self.tenant_id,
                                         "service_type":service_type, "vehicle_id":vehicle_id, "booking_id":booking_id, "limit":limit}
                                
            
            ####A booking should always have a vehicle_id but booking will not always hav ea driver
                 
            logger.debug(f"I am in here for {service_type or booking_status or vehicle_id} for {self.role}")
            
            
            logger.debug(f"service_type{service_type}")
            if self.role.lower() == 'tenant':
                logger.debug(f"service_type{service_type}")
                      
                stmt = """select b.* , CONCAT(v.make,' ',v.model,' ',v.year) as vehicle, CONCAT(u.first_name,' ',u.last_name) as customer_name, CONCAT(d.first_name,' ',d.last_name) as driver_name
                    from bookings b join vehicles v on v.id = b.vehicle_id join users u on u.id = b.rider_id left join drivers d on d.id = b.driver_id
                    where b.tenant_id = :tenant_id and ((:booking_status is null or b.booking_status = :booking_status) 
                    and (:service_type is null or b.service_type = :service_type) 
                    and (:vehicle_id is null or b.vehicle_id=:vehicle_id))
                    and (:booking_id is null or b.id=:booking_id)
                    order by b.created_on desc
                    limit :limit
                    """
                
                booking_query = self.db.execute(text(stmt), execute_params)
                    
            elif self.role.lower() == 'driver':
                execute_params['driver_id'] = self.driver_id
                stmt = """select b.* , CONCAT(v.make,' ',v.model,' ',v.year) as vehicle, CONCAT(u.first_name,' ',u.last_name) as customer_name, CONCAT(d.first_name,' ',d.last_name) as driver_name
                    from bookings b join vehicles v on v.id = b.vehicle_id join users u on u.id = b.rider_id left join drivers d on d.id = b.driver_id
                    where b.tenant_id = :tenant_id and b.driver_id = :driver_id and ((:booking_status is null or b.booking_status = :booking_status) 
                    and (:service_type is null or b.service_type = :service_type) 
                    and (:vehicle_id is null or b.vehicle_id=:vehicle_id))
                    and (:booking_id is null or b.id=:booking_id)
                    order by b.created_on desc
                    limit :limit"""
                booking_query = self.db.execute(text(stmt), execute_params)
                
                
            elif self.role.lower() == 'rider':
                execute_params['rider_id'] = self.rider_id
                
                stmt = """select b.* , CONCAT(v.make,' ',v.model,' ',v.year) as vehicle, CONCAT(u.first_name,' ',u.last_name) as customer_name, CONCAT(d.first_name,' ',d.last_name) as driver_name
                    from bookings b join vehicles v on v.id = b.vehicle_id join users u on u.id = b.rider_id left join drivers d on d.id = b.driver_id
                    where b.tenant_id = :tenant_id and b.rider_id = :rider_id and ((:booking_status is null or b.booking_status = :booking_status) 
                    and (:service_type is null or b.service_type = :service_type) 
                    and (:vehicle_id is null or b.vehicle_id=:vehicle_id))
                    and (:booking_id is null or b.id=:booking_id)
                    order by b.created_on desc
                    limit :limit"""
                booking_query = self.db.execute(text(stmt), execute_params)
            
            det = f"There are no bookings right now...."
            msg = f"bookings retrieved successfully"
            meta = None
           
            booking_obj:object = booking_query.all()
            
            if not booking_obj:
                return success_resp(meta={"status" :404},
                                    data=booking_obj, msg=det)
                    
            return success_resp(data=booking_obj, msg=msg, meta={"count":len(booking_obj), **meta}) if meta != None else success_resp(data=booking_obj, msg=msg, meta={"count":len(booking_obj)})
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)
            
    async def _get_driver_fullname(self, driver_id):
        

        driver = self.db.query(driver_table).filter(driver_table.id == driver_id).first()
        if not driver:
            logger.debug("Driver not in db")
            HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not in db")
        logger.info(f"{driver.full_name} is the driver for this ride ")
        return driver

    async def _get_vehicle(self, vehicle_id):

        vehicle = self.db.query(vehicle_table).filter(vehicle_table.id == vehicle_id).first()
        if not vehicle:
            logger.info(f"There are no vehicles with {vehicle_id}")
        return f"{vehicle.make} {vehicle.model} {vehicle.year}"
    def _bookings_overlap(self, payload):
     #check for overlaps
        try:
            exists = self.db.query(booking_table).filter(booking_table.vehicle_id == payload.vehicle_id).all()
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
            db_exceptions.handle(e, self.db)
        
    async def _price_quote(self, payload, distance):
        try: 
            logger.debug(f"tenant id {self.current_user.tenant_id}")

            pricing = self.db.query(tenant_pricing).filter(tenant_pricing.tenant_id == self.tenant_id).first()
            
            vehicle = self.db.query(vehicle_table).filter(vehicle_table.id == payload.vehicle_id).first()
            if not vehicle:
                logger.error(f"Tenant[{self.current_user.tenant_id}] Vehicle was not found at {payload.vehicle_id}")

                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail = "Vehicle not found")
            
            vehicle_base_price = self.db.query(vehicle_category_table).filter(vehicle_category_table.id == vehicle.vehicle_category_id).first()
            if not vehicle_base_price:
                logger.error(f"Tenant[{self.current_user.tenant_id}] Vehicle categroy was not found at {vehicle.vehicle_category_id}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail = "Vehicle category not found")
            if not pricing:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail= "pricing config for tenants not found...")
            #calculate price
            logger.info(f"base_fare = {pricing.base_fare}")
            base_fare = pricing.base_fare
            per_mile_rate = pricing.per_mile_rate 
            
            per_minute_rate = pricing.per_minute_rate 
            vehicle_rate = vehicle_base_price.vehicle_flat_rate
            min_duration = (distance/45) * 360
            total_quote = base_fare + (per_mile_rate * distance) + (per_minute_rate * min_duration) + vehicle_rate 
            
            if payload.service_type.lower() == "hourly":
                per_hour_rate = pricing.per_hour_rate
                hours = payload.hour
                total_quote = total_quote + (per_hour_rate * hours)

            return round(total_quote, 2)

        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)


def get_booking_service(db = Depends(get_db), current_user = Depends(deps.get_current_user)):
    return BookingService(db = db, current_user=current_user)
def get_unauthorized_booking_service(db = Depends(get_db)):
    return BookingService(db = db)
