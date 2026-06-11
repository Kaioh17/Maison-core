from fastapi import HTTPException, status
from fastapi.params import Depends
from app.models import booking, tenant, driver, vehicle_config, vehicle
from app.utils import db_error_handler
from app.utils.logging import logger
from datetime import timedelta, datetime
from sqlalchemy.exc import *
from app.db.database import get_db, get_base_db

from app.models import tenant_setting
from app.utils import password_utils
from .email_services import admin as admin_email
from app.config import Settings
from .service_context import ServiceContext
from .helper_service import *
from .email_services.tenants import TenantEmailServices
from ..core import deps

settings = Settings()

db_exceptions = db_error_handler.DBErrorHandler

# tenant_table = tenant.Tenants
# driver_table = driver.Drivers
# vehicle_table = vehicle.Vehicles
# booking_table = booking.Bookings
# vehicle_category_table = vehicle_category_rate.VehicleCategoryRate

class AdminService(ServiceContext):
    def __init__(self, current_user, db):
        super().__init__(db, current_user)
    async def create_admin(self, payload):
        data = payload.model_dump()
        response = self.db.query(admin_table).filter(admin_table.email == payload.email).first()
        if response:
            logger.error(f"Cannot signup with existing email")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Cannot signup with existing email")
        hashed_pwd = password_utils.hash(payload.password) #hash password

        new_admin = admin_table(**data)
        new_admin.password = hashed_pwd
        self.db.add(new_admin)
        self.db.commit()
        self.db.refresh(new_admin)
        logger.info('New admin added')
        return new_admin
    async def delete_tenant(self, tenant_id: int):
        tenant= self.db.query(tenant_table).filter_by(id=tenant_id).first()
        if not tenant:
            logger.error(f"Tenant {tenant_id} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                                detail = f"Tenant {tenant_id} not found")
        company_name = tenant.profile.company_name if hasattr(tenant, 'profile') and tenant.profile else None
        self.db.delete(tenant)
        self.db.commit()
        logger.info(f"Tenant {tenant_id} has been deleted")
        
        # Email: Notify admin of tenant deletion
        admin_email.AdminEmailServices(to_email=f'admin@{settings.domain}', from_email='noreply').tenant_deletion_confirmation_email(
            tenant_id=tenant_id,
            company_name=company_name,
            deleted_by='admin'
        )
        
        return {"msg": f"Tenant {tenant_id} has been deleted"}

    async def get_all_tenants(self):
        logger.debug("Getting all tenant info....")
        # TODO: Add more information getting all tenants
        tenants= self.db.query(tenant_table).all()

        if not tenants:
            logger.error(f"There are no refistered tenants at the moment..")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                                detail = f"There are no registered tenants at the moment..")
        
        # logger.info("There is a toatal of ")
        return tenants
    async def get_tenant_detail(self, tenant_id: int):
        """Aggregate a single tenant with every related model expanded.

        Powers the admin tenant-detail page. Relationships defined on the
        Tenants model (profile, stats, settings, branding, pricing,
        booking_pricing, drivers, users, vehicle, bookings) are read via the
        ORM; payouts and transactions are not relationships on Tenants, so
        they are queried directly by tenant_id.
        """
        from app.schemas import admin as admin_schema
        from app.models import payout as payout_model, transactions as transaction_model

        tenant_obj: tenant_table = (
            self.db.query(tenant_table).filter(tenant_table.id == tenant_id).first()
        )
        if not tenant_obj:
            logger.error(f"Tenant {tenant_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found",
            )

        drivers = list(tenant_obj.drivers or [])
        riders = list(tenant_obj.users or [])
        vehicles = list(tenant_obj.vehicle or [])
        bookings = list(tenant_obj.bookings or [])
        booking_pricing = list(tenant_obj.booking_pricing or [])


        payouts = (
            self.db.query(payout_model.Payout)
            .filter(payout_model.Payout.tenant_id == tenant_id)
            .all()
        )
        transactions = (
            self.db.query(transaction_model.Transaction)
            .filter(transaction_model.Transaction.tenant_id == tenant_id)
            .all()
        )

        payload = {
            "account": tenant_obj,
            "profile": tenant_obj.profile,
            "stats": tenant_obj.stats,
            "settings": tenant_obj.settings,
            "branding": tenant_obj.branding,
            "pricing": tenant_obj.pricing,
            "booking_pricing": booking_pricing,
            "drivers": drivers,
            "riders": riders,
            "vehicles": vehicles,
            "bookings": bookings,
            "payouts": payouts,
            "transactions": transactions,
            "counts": {
                "drivers": len(drivers),
                "riders": len(riders),
                "vehicles": len(vehicles),
                "bookings": len(bookings),
                "booking_pricing": len(booking_pricing),
                "payouts": len(payouts),
                "transactions": len(transactions),
            },
        }

        logger.debug(f"Payload {payload}")

        logger.info(f"Aggregated detail for tenant {tenant_id}")
        # return payload
        return admin_schema.AdminTenantDetail.model_validate(payload, from_attributes=True)

    async def override_verified_tenant(self, tenant_id: int, permission: bool):
        """Force-verify a tenant when webhook-driven verification fails."""
        validator = Validations(self.db)
        tenant_obj: tenant_table = validator._tenants_exist(tenant_id=tenant_id)

        if tenant_obj.is_verified and tenant_obj.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tenant already verified and active",
            )

        if not permission:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Explicit permission is required for forced verification",
            )

        tenant_obj.is_verified = True
        tenant_obj.is_active = True
        self.db.commit()
        self.db.refresh(tenant_obj)
        logger.info(f"Tenant {tenant_id} was force-verified by admin.")

        try:
            TenantEmailServices(
                to_email=tenant_obj.email,
                from_email='noreply',
                display_name='Maison',
            ).onboarding_email()
        except Exception as exc:
            logger.warning(f"Force verification email failed for tenant {tenant_id}: {exc}")

        return success_resp(
            msg="Successfully force-verified tenant",
            data={
                "tenant_id": tenant_obj.id,
                "is_verified": tenant_obj.is_verified,
                "is_active": tenant_obj.is_active,
            },
        )

    async def send_stripe_completion_reminder(self, tenant_id: int):
        """Email a tenant a fresh Stripe onboarding link to finish account setup.

        Used by admins to nudge tenants whose Stripe Connect account exists but
        is not yet fully onboarded (charges disabled). Generates a new
        `AccountLink` (existing ones expire) and emails it to the tenant.
        """
        import stripe

        tenant_obj: tenant_table = (
            self.db.query(tenant_table).filter(tenant_table.id == tenant_id).first()
        )
        if not tenant_obj:
            logger.error(f"Tenant {tenant_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found",
            )

        profile = tenant_obj.profile
        account_id = profile.stripe_account_id if profile else None
        if not account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant has no Stripe account yet — nothing to complete.",
            )
        if profile.charges_enabled:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tenant's Stripe account is already fully set up.",
            )

        stripe.api_key = settings.stripe_secret_key
        try:
            account_link = stripe.AccountLink.create(
                account=account_id,
                refresh_url=f"{settings.base_url}/tenant/reauth",
                return_url=f"{settings.base_url}/tenant/return",
                type="account_onboarding",
                collection_options={"fields": "eventually_due"},
            )
        except Exception as exc:
            logger.error(f"Failed to create Stripe account link for tenant {tenant_id}: {exc}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Could not generate a Stripe onboarding link.",
            )

        try:
            TenantEmailServices(
                to_email=tenant_obj.email,
                from_email='noreply',
                display_name='Maison',
            ).stripe_completion_reminder_email(tenant_obj, account_link.url)
        except Exception as exc:
            logger.error(f"Stripe completion reminder email failed for tenant {tenant_id}: {exc}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Generated the link but failed to send the reminder email.",
            )

        logger.info(f"Stripe completion reminder sent to tenant {tenant_id}")
        return success_resp(
            msg="Stripe completion reminder sent",
            data={"tenant_id": tenant_obj.id, "email": tenant_obj.email},
        )

    async def compose_email_to_tenant(self, payload):
        """Send an admin-authored freeform email to a specific tenant.

        `payload.from_alias` is the mailbox local part (e.g. 'noreply',
        'support') — `_format_from` on `AdminEmailServices` turns it into a
        full From header using the platform domain, matching how every other
        transactional email is built.
        """
        from app.schemas.admin import AdminComposeEmail

        tenant_obj: tenant_table = (
            self.db.query(tenant_table).filter(tenant_table.id == payload.to_tenant_id).first()
        )
        if not tenant_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {payload.to_tenant_id} not found",
            )

        try:
            admin_email.AdminEmailServices(
                to_email=tenant_obj.email,
                from_email=payload.from_alias,
                display_name='Maison',
            ).composed_email(subject=payload.subject, plain_body=payload.body)
        except Exception as exc:
            logger.error(f"Composed email failed for tenant {payload.to_tenant_id}: {exc}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to send email.",
            )

        logger.info(f"Admin composed email sent to tenant {payload.to_tenant_id} ({tenant_obj.email})")
        return success_resp(
            msg="Email sent",
            data={"tenant_id": tenant_obj.id, "to": tenant_obj.email},
        )

    async def get_logs(self, tail: int = 200):
        from pathlib import Path
        from app.schemas.admin import LogsResponse

        logs_dir = Path(__file__).resolve().parent.parent.parent / "logs"
        log_filename = (
            "maison_production.log"
            if settings.environment.lower() == "production"
            else "maison_dev.log"
        )
        log_path = logs_dir / log_filename

        if not log_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Log file not found: {log_filename}",
            )

        all_lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        tailed = all_lines[-tail:] if tail > 0 else all_lines
        return LogsResponse(
            log_file=log_filename,
            lines=tailed,
            total_lines=len(all_lines),
            environment=settings.environment,
        )

    async def override_verfied_tenant(self, tenant_id: int, permission: bool):
        """Backward-compatible typo alias; prefer override_verified_tenant."""
        return await self.override_verified_tenant(tenant_id=tenant_id, permission=permission)
       
        
def get_admin_service(db = Depends(get_db), current_user = Depends(deps.get_current_user)):
    return AdminService(db = db, current_user=current_user)
def unauthenticated_admin_service(db=Depends(get_base_db)):
    """No JWT: use get_base_db — get_db would require Bearer via get_tenant_id_from_token."""
    return AdminService(db=db, current_user=None)