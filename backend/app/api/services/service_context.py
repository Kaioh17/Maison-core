
from datetime import datetime, timezone
from app.db.database import get_db, get_base_db
from .helper_service import tenant_profile
from app.domain.plans import FREE_PLAN, FLEET_PLAN, SubStatus, resolve_plan, resolve_status


class ServiceContext:
    def __init__(self, db, current_user):
        """
        Docstring for __init__
        
        :param self: Description
        :param db: Description
        :param current_user: Description
        """
        self.RESERVED_SLUGS = {'api', 'www'}
        
        self.db = db
        self.current_user=current_user
        # Billing defaults, so every service can read self.plan / self.sub_status
        # unconditionally -- including unauthorized services where current_user
        # is None.
        self.profile_response = None
        self.plan = FREE_PLAN
        self.sub_plan = FREE_PLAN.name
        self.sub_status = SubStatus.INACTIVE.value
        if self.current_user:
            self.role = self.current_user.role
            if self.role != 'tenant' and self.role != 'admin': #not tenant
                self.tenant_id = self.current_user.tenant_id
                # print(self.tenant_id)
                # self.current_user.tenants
                self.tenant_email = self.current_user.tenants.email
                self.full_name = self.current_user.full_name
                if self.role== 'driver':
                    self.driver_id = self.current_user.id
                    self.driver_type = self.current_user.driver_type
                else:
                    self.rider_id = self.current_user.id
                    self.slug = self.current_user.tenants.slug
                self._resolve_billing(self.tenant_id)
            elif self.role == 'admin':
                # Admin tooling acts across tenants and must never be quota-blocked.
                self.plan = FLEET_PLAN
                self.sub_plan = FLEET_PLAN.name
                self.sub_status = SubStatus.ACTIVE.value
            else: # is tenant
                self.tenant_id = self.current_user.id
                self.tenant_email = self.current_user.email
                self.slug = self.current_user.profile.slug
                self._resolve_billing(self.tenant_id)

        self.time_now = datetime.now(timezone.utc)

    def _resolve_billing(self, tenant_id):
        """Resolve the acting tenant's plan and subscription status.

        Runs for every role that acts on behalf of a tenant, not just tenants
        themselves -- drivers and riders reach quota-consuming paths too. Uses
        getattr so a missing profile row degrades to the free plan instead of
        raising AttributeError.
        """
        self.profile_response = self.db.query(tenant_profile).filter(
            tenant_profile.tenant_id == tenant_id
        ).first()
        self.plan = resolve_plan(getattr(self.profile_response, "subscription_plan", None))
        self.sub_plan = self.plan.name
        # NB: the column is subscription_status; the previous commented-out line
        # misspelled it as `subscripton_status`, which is why it was never wired up.
        self.sub_status = resolve_status(
            getattr(self.profile_response, "subscription_status", None)
        )
                        
                                
# def get_service_(db = Depends(get_db), current_user = Depends(deps.get_current_user)):
#     return BookingService(db = db, current_user=current_user)
# def get_unauthorized_booking_service(db = Depends(get_db)):
#     return BookingService(db = db)