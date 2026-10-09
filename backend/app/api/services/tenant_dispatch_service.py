"""Tenant-side dispatch: which vehicles are assigned to which drivers, and which driver takes which booking."""
from fastapi import HTTPException, Depends, status
from app.models import driver, vehicle, booking
from app.utils import db_error_handler
from app.utils.logging import logger
from app.db.database import get_db
from ..core import deps
from .helper_service import success_resp, user_table
from .email_services import drivers
from .service_context import ServiceContext
from .tenant_driver_service import TenantDriverService


class TenantDispatchService(ServiceContext):
    db_exceptions = db_error_handler.DBErrorHandler
    driver_table = driver.Drivers
    vehicle_table = vehicle.Vehicles
    booking_table = booking.Bookings

    async def get_all_vehicles(self):
        try:
            logger.info(f"Getting vehicles for tenant: {self.tenant_id}")
            vehicle_query = self.db.query(self.vehicle_table).filter(self.vehicle_table.tenant_id == self.tenant_id)
            vehicle_obj = vehicle_query.all()

            if not vehicle_obj:
                logger.info(f"There are no vehicles for tenant {self.tenant_id}")
                return success_resp(data=[], msg="Vehicles retrieved successfully", meta={"count": 0})

            return success_resp(data=vehicle_obj, msg="Vehicles retrieved successfully", meta={"count": len(vehicle_obj)})
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.error(f"Unexpected error in get_all_vehicles: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def fetch_assigned_drivers_vehicles(self):
        try:
            
            logger.info(f"Getting vehicles with assigned drivers for tenant: {self.tenant_id}")
            vehicle_query = self.db.query(self.vehicle_table).filter(self.vehicle_table.tenant_id == self.tenant_id,
                                                            self.vehicle_table.driver_id != None)
            vehicle_obj = vehicle_query.all()
                    

            if not vehicle_obj:
                logger.warning(f"There are no vehicles assigned to any drivers {self.tenant_id}")
                raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,
                                    detail = f"Tenant {self.tenant_id} has no vehicles assigned to any drivers")
            return success_resp(data=vehicle_obj, msg="Vehicles with assigned drivers retrieved successfully", meta={"count": len(vehicle_obj)})
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)

    async def find_vehicles_owned_by_driver(self, driver_id: int):
        try:
            await TenantDriverService(self.db, self.current_user).validate_driver_id(driver_id)
            logger.info(f"Getting vehicles with assigned drivers for tenant: {self.tenant_id}")
            vehicle_query = self.db.query(self.vehicle_table).filter(self.vehicle_table.tenant_id == self.tenant_id,
                                                            self.vehicle_table.driver_id == driver_id)
            vehicle_obj = vehicle_query.all()
                    

            if not vehicle_obj:
                logger.warning(f"Driver {driver_id} does not have an assigned a vehicle {self.tenant_id}")
                raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,
                                    detail = f"Driver {driver_id} does not have an assigned a vehicle {self.tenant_id}")
            return success_resp(data=vehicle_obj, msg=f"Vehicles for driver {driver_id} retrieved successfully", meta={"count": len(vehicle_obj), "driver_id": driver_id})
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)

    async def assign_driver_to_vehicle(self, driver_id, vehicle_id):
        """A tenant can only assign a vehicle to one driver at a time"""
        try:
            vehicle_ =  self.db.query(self.vehicle_table).filter(self.vehicle_table.driver_id == driver_id, self.vehicle_table.tenant_id == self.tenant_id).first()
            if vehicle_:
                logger.warning(f"Driver already has a vehicle [{vehicle_.vehicle_name}]")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail= f"Driver already has a vehicle [{vehicle_.vehicle_name}]")
            vehicle =  self.db.query(self.vehicle_table).filter(self.vehicle_table.id == vehicle_id, self.vehicle_table.tenant_id == self.tenant_id).first()

            if not vehicle:
                logger.warning("This vehicle does not exist")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail= "This vehicle does not exist")
            if vehicle.driver_id:
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                                    detail = "Vehicle already assigned to a driver.If you need to assign this driver unassign the current driver from that vehicle.")
            driver_info = self.db.query(self.driver_table).filter(self.driver_table.id == driver_id, self.driver_table.tenant_id == self.tenant_id).first()
            if not driver_info:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail= "Driver info does not exists")
            if driver_info.driver_type == None and driver_info.driver_type != "in_house":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, 
                                    detail="Outsourced drivers cannot be assigned to rides...")
                
            vehicle.driver_id = driver_id

            self.db.commit()
            
            # Email: Send vehicle assignment notification to driver
            if driver_info:
                drivers.DriverEmailServices(to_email=driver_info.email, from_email='notifications', display_name=self.slug).vehicle_assignment_email(
                    obj=driver_info,
                    vehicle_obj=vehicle
                )
            
            return success_resp(data={"driver_id": driver_id, "vehicle_id": vehicle_id}, msg=f"Driver {driver_id} has been assigned to vehicle: {vehicle_id}")
            
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)

    async def assign_driver_to_rides(self, payload, booking_id: int):
       try:
            """We can only assign a driver with a vehicle to the pla"""
            ride =  self.db.query(self.booking_table).filter(self.booking_table.id == booking_id, self.booking_table.tenant_id == self.tenant_id).first()

            if not ride:
                logger.warning(f"There is no booking with this id {booking_id}...")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail= f"There is no booking with this id {booking_id}....")
            if ride.driver_id and payload.override != True:
                logger.warning("Driver already assigned to ride....")
                raise HTTPException(status_code=404,
                                   detail = "Driver already assigned to ride....")
            
            driver_info = self.db.query(self.driver_table).filter(self.driver_table.id == payload.driver_id, self.driver_table.tenant_id == self.tenant_id).first()
            if not driver_info:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail= "Driver info does not exists")
            if driver_info.driver_type == None and driver_info.driver_type != "in_house":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, 
                                    detail="outsourced drivers cannot be assigned to rides...")
            
            if not driver_info.is_active:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail="Deactivated drivers cannot be assigned to rides.")

            ride.driver_id = payload.driver_id

            self.db.commit()
            
            """Email Notificaition"""
            rider_row = self.db.query(user_table).filter(user_table.id == ride.rider_id).first()
            rider_nm = rider_row.full_name if rider_row else None
            rider_phone = rider_row.phone_no if rider_row else None
            drivers.DriverEmailServices(to_email=driver_info.email, from_email='notifications', display_name=self.slug).new_ride(
                booking_obj=ride, assigned=True, slug=self.slug, rider_name=rider_nm, rider_phone=rider_phone
            )
            return success_resp(data={"driver_id": payload.driver_id, "booking_id": booking_id}, msg=f"Driver {payload.driver_id} has been assigned to {booking_id}")
       except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)

    async def unassign_driver_from_vehicles(self, override, vehicle_id):
        try:
            if override:
                
                vehicle =  self.db.query(self.vehicle_table).filter(self.vehicle_table.id == vehicle_id, self.vehicle_table.tenant_id == self.tenant_id).first()

                if not vehicle:
                    logger.warning("Vehicle not found....")
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                        detail= "Vehicle not found....")
                if not vehicle.driver_id:
                    raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                                        detail = "Vehicle does not have a driver to unassign")
                
                if not vehicle.driver_type or vehicle.driver_type != 'in_house':
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, 
                                        detail="Outsourced drivers cannot be unassigned from their vehicles...")
                
                # Store driver info for email before unassigning
                driver_email = vehicle.driver.email
                driver_obj = vehicle.driver
                unassigned_driver_id = vehicle.driver_id
                logger.debug(unassigned_driver_id)
                # Unassign the driver from the vehicle
                vehicle.driver_id = None

                self.db.commit()
                
                # Email: Send vehicle unassignment notification to driver
                drivers.DriverEmailServices(to_email=driver_email, from_email='notifications', display_name=self.slug).vehicle_unassignment_email(
                    obj=driver_obj,
                    vehicle_obj=vehicle
                )
                
                return success_resp(msg=f"Driver {unassigned_driver_id} has been unassigned from vehicle: {vehicle_id}")
            else:
                return success_resp(msg=f"unassign process has been cancelled")
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)


def get_tenant_dispatch_service(db=Depends(get_db), current_user=Depends(deps.get_current_user)):
    return TenantDispatchService(db=db, current_user=current_user)
