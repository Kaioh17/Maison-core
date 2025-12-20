

"""
Service layer for tenant-related operations in the Maison-core backend.
This module provides functions to manage tenants, drivers, vehicles, and bookings, including creation, retrieval, onboarding, and approval processes. It handles database interactions, enforces unique constraints, and manages error handling for common DB exceptions. The service also includes helper functions for tenant settings setup, driver email validation, and onboarding token generation.
Key functionalities:
- Tenant creation and settings initialization
- Retrieval of company, driver, vehicle, and booking information
- Onboarding and approval workflows for drivers
- Vehicle assignment and ownership queries
- Error handling and logging for all operations
Dependencies:
- FastAPI for HTTP exception handling
- SQLAlchemy ORM models for tenants, drivers, vehicles, bookings, and tenant settings
- Utility modules for password hashing, database error handling, and logging
"""
import os
from typing import Optional
from fastapi import HTTPException, UploadFile, status, Form, File, Depends
from sqlalchemy import text
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from pydantic import EmailStr
from app.models import tenant, driver, TenantSettings, vehicle, booking, vehicle_category_rate
from app.utils import password_utils, db_error_handler
from app.utils.logging import logger
from datetime import datetime, timedelta 
import random
from .stripe_services import StripeService
import string
from .booking_services import _get_driver_fullname, _get_vehicle
from app.db.database import get_db, get_base_db
from ..core import deps
# from .helper_service import 

class TenantService:
    def __init__(self, db, current_tenants):
        self.db = db
        self.current_tenants = current_tenants
    db_exceptions = db_error_handler.DBErrorHandler

    # tenant_table = tenant.Tenants
    tenant_info = tenant.Tenants
    tenant_profile = tenant.TenantProfile
    tenant_stats = tenant.TenantStats

    driver_table = driver.Drivers
    vehicle_table = vehicle.Vehicles
    booking_table = booking.Bookings
    vehicle_category_table = vehicle_category_rate.VehicleCategoryRate

    async def create_tenant(self, email,
                             first_name,
                             last_name ,
                            password ,
                            phone_no ,
                            company_name ,
                            # logo_url: Optional[UploadFile] = None
                            slug ,
                            address ,
                            city ,
                            drivers_count ,
                            logo_url ):
        try:
            print("the new method...")
            model_map = {
                "email": email,
                # "company_name": company_name,
                "phone_no": phone_no,
                # "slug": slug
            }
            self._check_unique_fields(self.tenant_info, model_map)
            
            """Stripe config"""
            stripe_customer = StripeService.create_customer(email = email,name = f"{first_name} {last_name}")
            stripe_express = StripeService.create_express_account(email = email)

            """Create new tenants"""
            logo_path = await self._verify_upload(logo_url,slug)

            hashed_pwd = password_utils.hash(password.strip()) #hash password
          
            new_tenant_info = self.tenant_info( email=email,
                                        first_name=first_name,
                                        last_name=last_name,
                                        password=hashed_pwd,
                                        phone_no=phone_no)
            # new_tenant_info.password = hashed_pwd
            
            self.db.add(new_tenant_info)
            self.db.commit()
            self.db.refresh(new_tenant_info)
            new_tenant_id = new_tenant_info.id
            logger.debug(f"New tenant id: {new_tenant_id}")
            new_tenant_profile = self.tenant_profile(tenant_id = new_tenant_id,
                                                     company_name=company_name,
                                                    slug=slug,
                                                    address=address,
                                                    city=city,                                
                                                    logo_url = logo_path,
                                                    stripe_customer_id = stripe_customer,
                                                    stripe_account_id = stripe_express,
                                                    )
            new_tenant_stats = self.tenant_stats(tenant_id = new_tenant_id, 
                                                 drivers_count=drivers_count)

        
        
            self.db.add(new_tenant_profile)
            self.db.add(new_tenant_stats)
            
            self.db.commit()
            self.db.refresh(new_tenant_profile)
            self.db.refresh(new_tenant_stats)

            # logger.info(f"new tenant_id {new_tenant.id}")
            response_dict  = {"tenants": new_tenant_info, "profile": new_tenant_profile, "stats": new_tenant_stats}
            """add tenants settings"""
            logger.debug(response_dict)
            await self._set_up_tenant_settings(new_tenant_id, logo_path, slug)
            await self._create_vehicle_category_rate_table(new_tenant_id)

        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)
        
        return response_dict
    def _check_unique_fields(self, model, fields: dict):
        try:
            for field_name, value in fields.items():
                column = getattr(model, field_name)
                exists = self.db.query(model).filter(column == value).first()
                if exists:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"{field_name.replace('_', ' ').title()} already exists"
                    )
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)
            
    async def get_company_info(self):
        try: 
            # company = db.execute(text("select * from tenants t join tenants_profile tp on tp.tenant_id = t.id join tenant_stats ts on ts.tenant_id = t.id where tenant_id = "))
            stmt = self.db.query(self.tenant_info).options(
                        joinedload(self.tenant_info.profile),
                        joinedload(self.tenant_info.stats)
                    ).where(self.tenant_info.id == self.current_tenants.id)
            result = self.db.execute(stmt).scalars().first()

            if not result:
                logger.warning(f"404: company with id {self.current_tenants.id} is not in db")
                raise HTTPException(status_code=404,
                                    detail="Company cannot be found")
            
            return result
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)
            raise HTTPException(status_code=500, detail="Database error occurred")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_company_info: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    async def _set_up_tenant_settings(self, new_tenant_id, logo_url, slug):
        try: 
            new_tenants_settings = TenantSettings(
                tenant_id = new_tenant_id,
                logo_url = logo_url, 
                slug = slug,
                theme = "dark",  # Default theme
                enable_branding = False,  # Default to false
                base_fare = 0.0,  # Default base fare
                per_mile_rate = 0.0,  # Default per mile rate
                per_minute_rate = 0.0,  # Default per minute rate
                per_hour_rate = 0.0,  # Default per hour rate
                rider_tiers_enabled = False,  # Default to false
                cancellation_fee = 0.0,  # Default cancellation fee
                discounts = False  # Default to false
            )
            self.db.add(new_tenants_settings)
            self.db.commit()
            logger.info(f"Tenant settings created for tenant_id: {new_tenant_id}")
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)
            
    async def _create_vehicle_category_rate_table(self, id_tenant):
        try:
            logger.info("Setting new tenant vehicle settings table..")
            vehicle_category = [
                self.vehicle_category_table(tenant_id = id_tenant,vehicle_category = "Luxury Sedan"),
                self.vehicle_category_table(tenant_id = id_tenant,vehicle_category = "Executive SUV"),
                self.vehicle_category_table(tenant_id = id_tenant,vehicle_category = "Stretch Limo"),
                self.vehicle_category_table(tenant_id = id_tenant,vehicle_category = "Business Van")

            ]

            self.db.add_all(vehicle_category)
            self.db.commit()
            
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)
    
    async def _verify_upload(self, logo_url,slug):
        if logo_url:
            try:
                contents = await logo_url.read()
                # Extract filename from the uploaded file
                filename = logo_url.filename if hasattr(logo_url, 'filename') else 'logo.jpg'
                upload_dir =  "app/upload/logos"
                os.makedirs(upload_dir, exist_ok=True)
                file_path = f"{upload_dir}/{slug}_{filename}"
                with open(file_path, "wb") as f:
                    f.write(contents)
                logger.info(f"{file_path}")
                logger.info("{slug}, Logo is saved!!")
                return file_path
            except Exception as e:
                logger.warning(f"Failed to save logo upload: {e}")
                # Continue without failing the tenant creation
        return None

    async def get_all_drivers(self):
        try:
            logger.info(f"Getting all drivers for {self.current_tenants.id}")
            drivers_query = self.db.query(self.driver_table).filter(self.driver_table.tenant_id == self.current_tenants.id)
            drivers = drivers_query.all()

            if not drivers:
                logger.info(f"There are no drivers for tenant {self.current_tenants.id}")
                return []

            return drivers
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.error(f"Unexpected error in get_all_drivers: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def _validate_driver_id(self, driver_id):
        try:
            exists = self.db.query(self.driver_table).filter(self.driver_table.id == driver_id, 
                                                self.driver_table.tenant_id == self.current_tenants.id).first()
            if not exists:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail= f"Driver with {driver_id} does not exists") 
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)

    async def _confirm_driver_email_absence(self, payload):
        ##verify_email does not exist
        try:
            driver_exists = self.db.query(self.driver_table).filter(self.driver_table.email == payload.email,
                                                    self.driver_table.tenant_id == self.current_tenants.id).first()

            if driver_exists: 
                logger.warning("Driver with email already exists...")
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail = "Driver with email already exists...")
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)

    async def _onboarding_token(self, length = 10):
        access_token = string.ascii_letters + string.digits
        return ''.join(random.choices(access_token, k=length))

    async def onboard_drivers(self, payload):
        try:
            await self._confirm_driver_email_absence(payload)
            onboard_token = await self._onboarding_token(6)
            logger.info("Starting onboarding process....")
            driver_info = payload.model_dump()
            driver_info.pop("users", None)
            new_driver = self.driver_table(tenant_id = self.current_tenants.id,
                                      driver_token = onboard_token, 
                                      is_registered = "pending",**driver_info)


            self.db.add(new_driver)
            self.db.commit()
            self.db.refresh(new_driver)
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)

        logger.info("Onboarding process complete...")

        return new_driver

    async def approve_driver(self, payload):
        try:
            # logger.info(approve_driver)
            pass
            
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)

    async def get_all_vehicles(self):
        try:
            logger.info(f"Getting vehicles for tenant: {self.current_tenants.id}")
            vehicle_query = self.db.query(self.vehicle_table).filter(self.vehicle_table.tenant_id == self.current_tenants.id)
            vehicle_obj = vehicle_query.all()

            if not vehicle_obj:
                logger.info(f"There are no vehicles for tenant {self.current_tenants.id}")
                return []  # Return empty array instead of raising error

            return vehicle_obj
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.error(f"Unexpected error in get_all_vehicles: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def fetch_assigned_drivers_vehicles(self):
        try:
            
            logger.info(f"Getting vehicles with assigned drivers for tenant: {self.current_tenants.id}")
            vehicle_query = self.db.query(self.vehicle_table).filter(self.vehicle_table.tenant_id == self.current_tenants.id,
                                                            self.vehicle_table.driver_id != None)
            vehicle_obj = vehicle_query.all()
                    

            if not vehicle_obj:
                logger.warning(f"There are no vehicles assigned to any drivers {self.current_tenants.id}")
                raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,
                                    detail = f"Tenant {self.current_tenants.id} has no vehicles assigned to any drivers")
            return vehicle_obj
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)

    async def find_vehicles_owned_by_driver(self, driver_id: int):
        try:
            await self._validate_driver_id(driver_id)
            logger.info(f"Getting vehicles with assigned drivers for tenant: {self.current_tenants.id}")
            vehicle_query = self.db.query(self.vehicle_table).filter(self.vehicle_table.tenant_id == self.current_tenants.id,
                                                            self.vehicle_table.driver_id == driver_id)
            vehicle_obj = vehicle_query.all()
                    

            if not vehicle_obj:
                logger.warning(f"Driver {driver_id} does not have an assigned a vehicle {self.current_tenants.id}")
                raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,
                                    detail = f"Driver {driver_id} does not have an assigned a vehicle {self.current_tenants.id}")
            return vehicle_obj
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)

    async def assign_driver_to_vehicle(self, payload, vehicle_id):
        try:
            vehicle =  self.db.query(self.vehicle_table).filter(self.vehicle_table.id == vehicle_id).first()

            if not vehicle:
                logger.warning("There are no bookings without assigned drivers....")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail= "There are no bookings without assigned drivers....")
            if vehicle.driver_id:
                raise HTTPException(status_code=404,
                                    detail = "Driver already assigned to ride....")
            driver_info = self.db.query(self.driver_table).filter(self.driver_table.id == payload.driver_id).first()
            if not driver_info:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail= "Driver info does not exists")
            if driver_info.driver_type == None and driver_info.driver_type != "in_house":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, 
                                    detail="Outsourced drivers cannot be assigned to rides...")
            vehicle.driver_id = payload.driver_id

            self.db.commit()
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)
        return {"msg": f"Driver {payload.driver_id} has been assigned to vehicle: {vehicle_id}"}

    async def get_all_bookings(self):
        try:
            booking_query = self.db.query(self.booking_table).filter(self.booking_table.tenant_id == self.current_tenants.id)
            booking_obj = booking_query.all()
            
            if not booking_obj:
                logger.info(f"There are no bookings for tenant {self.current_tenants.id}")
                return []  # Return empty array instead of raising error
            
            result = []
            for ride in booking_obj:
                driver_full_name = None
                vehicle = None
                
                if ride.driver_id:
                    driver_full_name = await _get_driver_fullname(driver_id=ride.driver_id, db=self.db)
                if ride.vehicle_id:
                    vehicle = await _get_vehicle(vehicle_id=ride.vehicle_id, db=self.db)
               

                ride_dict = ride.__dict__.copy()
                ride_dict["vehicle"] = vehicle
                ride_dict["driver_fullname"] = driver_full_name
                
                result.append(ride_dict)
                
        

            

            return result
            # return booking_obj
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.error(f"Unexpected error in get_all_bookings: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def get_bookings_by_status(self, booking_status: str):
        try:
            booking_query = self.db.query(self.booking_table).filter(self.booking_table.tenant_id == self.current_tenants.id,
                                                       self.booking_table.booking_status == booking_status.lower())

            booking_obj = booking_query.all()
            
            if not booking_obj:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail= f"There are no {booking_status} bookings right now....")
            return booking_obj
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)

    async def assign_driver_to_rides(self, payload, rider_id: int):
       try:
            ride =  self.db.query(self.booking_table).filter(self.booking_table.id == rider_id).first()

            if not ride:
                logger.warning("There are no bookings without assigned drivers....")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail= "There are no bookings without assigned drivers....")
            if ride.driver_id:
                raise HTTPException(status_code=404,
                                    detail = "Driver already assigned to ride....")
            
            driver_info = self.db.query(self.driver_table).filter(self.driver_table.id == payload.driver_id).first()
            if not driver_info:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail= "Driver info does not exists")
            if driver_info.driver_type == None and driver_info.driver_type != "in_house":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, 
                                    detail="outsourced drivers cannot be assigned to rides...")
            
            ride.driver_id = payload.driver_id

            self.db.commit()
            return {"msg": f"Driver {payload.driver_id} has been assigned to {rider_id}"}
       except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)

def get_tenant_service(db = Depends(get_db), current_tenants = Depends(deps.get_current_user)):
    return TenantService(db=db, current_tenants=current_tenants)
def get_unauthorized_tenant_service(db = Depends(get_db)):
    return TenantService(db=db, current_tenants=None)