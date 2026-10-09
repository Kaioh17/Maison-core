"""Tenant-side driver management: listing, onboarding, approval, activation and permanent deletion."""
import random
import secrets
import string
import redis
from fastapi import HTTPException, Depends, status
from sqlalchemy import func, select
from app.models import driver, booking, payout
from app.redis_connect import redis_client
from app.utils import db_error_handler
from app.utils.logging import logger
from app.db.database import get_db
from app.policies import plan_policy
from ..core import deps
from .helper_service import success_resp
from .email_services import drivers
from .service_context import ServiceContext


def count_drivers(db, tenant_id):
    """Number of driver rows a tenant owns (counts against the plan's driver quota)."""
    try:
        return db.scalar(select(func.count()).where(driver.Drivers.tenant_id == tenant_id))
    except db_error_handler.DBErrorHandler.COMMON_DB_ERRORS as e:
        db_error_handler.DBErrorHandler.handle(exc=e, db=db)


class TenantDriverService(ServiceContext):
    db_exceptions = db_error_handler.DBErrorHandler
    driver_table = driver.Drivers
    booking_table = booking.Bookings

    async def get_all_drivers(self, driver_id):
        try:
            logger.info(f"Getting all drivers for {self.tenant_id}")
            if driver_id:
                drivers_query = self.db.query(self.driver_table).filter(self.driver_table.tenant_id == self.tenant_id, self.driver_table.id == driver_id)
                drivers = drivers_query.all()    
            else:    
                drivers_query = self.db.query(self.driver_table).filter(self.driver_table.tenant_id == self.tenant_id)
                drivers = drivers_query.all()

            if not drivers:
                logger.info(f"There are no drivers for tenant {self.tenant_id}")
                return success_resp(data=[], msg="Drivers retrieved successfully", meta={"count": 0})

            return success_resp(data=drivers, msg="Drivers retrieved successfully", meta={"count": len(drivers)})
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.error(f"Unexpected error in get_all_drivers: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def validate_driver_id(self, driver_id):
        try:
            exists = self.db.query(self.driver_table).filter(self.driver_table.id == driver_id, 
                                                self.driver_table.tenant_id == self.tenant_id).first()
            if not exists:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail= f"Driver with {driver_id} does not exists") 
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)

    async def _confirm_driver_email_absence(self, payload):
        ##verify_email does not exist
        try:
            driver_exists = self.db.query(self.driver_table).filter(self.driver_table.email == payload.email,
                                                    self.driver_table.tenant_id == self.tenant_id).first()

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
            ##check policies
            cur_driver_count = count_drivers(self.db, self.tenant_id)
            logger.debug(f"DRiver counnt {cur_driver_count}")
            plan_policy.PlanPolicy.assert_can_onboard_driver(
                plan=self.plan,
                sub_status=self.sub_status,
                current_count=cur_driver_count,
            )
            await self._confirm_driver_email_absence(payload)
            onboard_token = await self._onboarding_token(6)
            logger.info("Starting onboarding process....")
            driver_info = payload.model_dump()
            driver_info.pop("users", None)
            new_driver = self.driver_table(tenant_id = self.tenant_id,
                                      driver_token = onboard_token, 
                                      is_registered = "pending",**driver_info)


            self.db.add(new_driver)
            self.db.commit()
            self.db.refresh(new_driver)
            
            """email notification"""
            drivers.DriverEmailServices(to_email=new_driver.email, from_email='driver', display_name=self.slug).onboarding_email(token=onboard_token, slug=self.slug)
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)

        logger.info("Onboarding process complete...")

        return success_resp(data=new_driver, msg="New driver onboarded successfully")

    async def approve_driver(self, driver_id: int):
        """
        Approves a driver row that is awaiting review -- either a self-serve
        application (see DriverService.apply) or a tenant invite the driver
        hasn't finished registering yet. Issues the onboarding token and
        emails the driver their registration link, same as `onboard_drivers`.
        """
        try:
            driver_obj = self.db.query(self.driver_table).filter(
                self.driver_table.id == driver_id,
                self.driver_table.tenant_id == self.tenant_id,
            ).first()
            if not driver_obj:
                logger.warning(f"Driver {driver_id} not found for tenant {self.tenant_id}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
            if driver_obj.is_registered == "registered":
                logger.warning(f"Driver {driver_id} is already registered")
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Driver is already registered")

            onboard_token = await self._onboarding_token(6)
            driver_obj.driver_token = onboard_token
            driver_obj.is_active = True
            self.db.commit()
            self.db.refresh(driver_obj)

            drivers.DriverEmailServices(
                to_email=driver_obj.email, from_email='driver', display_name=self.slug
            ).onboarding_email(token=onboard_token, slug=self.slug)

            logger.info(f"Driver {driver_id} approved")
            return success_resp(msg="Driver approved", data={"id": driver_obj.id})
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)

    # --- Permanent driver deletion (two steps, no schema change: the step-1 token lives in Redis) ---
    DRIVER_DELETE_TTL = 600

    def _driver_delete_key(self, driver_id: int) -> str:
        return f"driver_delete:{self.tenant_id}:{driver_id}"

    def _get_tenant_driver(self, driver_id: int):
        driver_obj = self.db.query(self.driver_table).filter(
            self.driver_table.id == driver_id,
            self.driver_table.tenant_id == self.tenant_id,
        ).first()
        if not driver_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
        return driver_obj

    def _driver_deletion_warnings(self, driver_obj) -> list[str]:
        """Raises 409 if history/fleet data forbids deletion; otherwise returns the warnings to show."""
        has_bookings = self.db.query(self.booking_table.id).filter(
            self.booking_table.driver_id == driver_obj.id).first()
        has_payouts = self.db.query(payout.Payout.id).filter(
            payout.Payout.driving_id == driver_obj.id).first()
        if has_bookings or has_payouts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This driver has booking or payout history, which must be kept. Deactivate the driver instead.",
            )

        warnings = [
            "This is permanent and cannot be undone. The driver cannot be restored.",
            "The driver's account and login are removed immediately.",
        ]
        vehicle_obj = driver_obj.vehicle
        if vehicle_obj:
            if driver_obj.driver_type == "in_house":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Unassign this driver's fleet vehicle before deleting the driver.",
                )
            if self.db.query(self.booking_table.id).filter(
                    self.booking_table.vehicle_id == vehicle_obj.id).first():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This driver's vehicle is used by existing bookings, so the driver cannot be deleted.",
                )
            warnings.append("The driver's vehicle is deleted along with the driver.")
        if driver_obj.stripe_account_id:
            warnings.append("The driver's Stripe account is not closed. Handle any remaining balance in Stripe.")
        return warnings

    async def request_driver_deletion(self, driver_id: int):
        try:
            driver_obj = self._get_tenant_driver(driver_id)
            warnings = self._driver_deletion_warnings(driver_obj)
            token = secrets.token_urlsafe(32)
            redis_client.set(self._driver_delete_key(driver_id), token, ex=self.DRIVER_DELETE_TTL)
            logger.info(f"Driver {driver_id} deletion requested by tenant {self.tenant_id}")
            return success_resp(
                msg="Review the warnings, then confirm to permanently delete this driver",
                data={
                    "driver_id": driver_obj.id,
                    "driver_name": driver_obj.full_name,
                    "warnings": warnings,
                    "confirmation_token": token,
                    "expires_in_seconds": self.DRIVER_DELETE_TTL,
                },
            )
        except redis.RedisError as e:
            logger.error(f"Redis unavailable for driver deletion: {e}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                detail="Deletion is temporarily unavailable. Try again shortly.")
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)

    async def delete_driver(self, driver_id: int, payload):
        try:
            driver_obj = self._get_tenant_driver(driver_id)
            key = self._driver_delete_key(driver_id)
            stored = redis_client.get(key)
            if not stored or not secrets.compare_digest(stored.decode(), payload.confirmation_token):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Confirmation expired or invalid. Start the deletion again.")
            if payload.confirm_email.lower() != driver_obj.email.lower():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="The email you typed does not match this driver.")
            self._driver_deletion_warnings(driver_obj)  # re-check blockers: state may have changed since step 1

            self.db.delete(driver_obj)
            self.db.commit()
            redis_client.delete(key)  # single use
            logger.warning(f"Driver {driver_id} permanently deleted by tenant {self.tenant_id}")
            return success_resp(msg="Driver permanently deleted", data={"id": driver_id})
        except redis.RedisError as e:
            logger.error(f"Redis unavailable for driver deletion: {e}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                detail="Deletion is temporarily unavailable. Try again shortly.")
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)

    async def set_driver_active(self, driver_id: int, is_active: bool):
        """Reversible alternative to deletion. Inactive drivers cannot be assigned new rides."""
        try:
            driver_obj = self._get_tenant_driver(driver_id)
            if driver_obj.is_registered != "registered":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail="Only registered drivers can be activated or deactivated. Approve pending drivers instead.")
            if driver_obj.is_active != is_active:
                driver_obj.is_active = is_active
                self.db.commit()
                drivers.DriverEmailServices(to_email=driver_obj.email, from_email='noreply', display_name=self.slug) \
                    .status_change_email(obj=driver_obj, is_active=is_active)
                logger.info(f"Driver {driver_id} set is_active={is_active} by tenant {self.tenant_id}")
            return success_resp(msg="Driver activated" if is_active else "Driver deactivated",
                                data={"id": driver_obj.id, "is_active": is_active})
        except self.db_exceptions.COMMON_DB_ERRORS as e:
            self.db_exceptions.handle(e, self.db)


def get_tenant_driver_service(db=Depends(get_db), current_user=Depends(deps.get_current_user)):
    return TenantDriverService(db=db, current_user=current_user)
