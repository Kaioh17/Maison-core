from fastapi import APIRouter, HTTPException, FastAPI, Response, status, Path, Query
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db, get_base_db
from app.schemas import tenant, general, admin
from app.utils.logging import logger
from ..services.admin_services import AdminService, get_admin_service, unauthenticated_admin_service

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
)


@router.delete(
    "/delete/{tenant_id}/tenant",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tenant (destructive)",
    description=(
        "**Admin only** — cascades tenant data per ORM. "
        "Protect with network policy / auth in production (currently open if router is mounted)."
    ),
    response_description="No content on success.",
    include_in_schema=False,
)
async def delete_tenant(
    tenant_id: int = Path(..., description="Tenant id to delete."),
    db: Session = Depends(get_base_db),
    admin_service: AdminService = Depends(get_admin_service)
):
    tenant = await admin_service.delete_tenant(db, tenant_id)
    return tenant


@router.get(
    "/tenants",
    status_code=status.HTTP_200_OK,
    response_model=general.StandardResponse[list[tenant.TenantResponse]],
    summary="List all tenants",
    description="Returns every tenant record for admin dashboards. **Unauthenticated** in code — lock down in production.",
    response_description="Standard response with tenant list and meta counts.",
    include_in_schema=False,
)
async def get_all_tenants(
    admin_service: AdminService = Depends(get_admin_service)
                          ):
    tenants = await admin_service.get_all_tenants()
    return general.StandardResponse(
        message="All tenants retrieved successfully",
        data=tenants,
        meta={"counts": len(tenants)},
    )
@router.post(
    "/",
    status_code=201,
    response_model=general.StandardResponse[admin.AdminResponse],
    summary="Create admin",
    description="Returns every tenant record for admin dashboards. ",
    response_description="Standard response with tenant list and meta counts.",
    include_in_schema=False,
)
async def create_admin(payload: admin.CreateAdmin,
                        admin_service: AdminService = Depends(unauthenticated_admin_service)
                          ):
    admin = await admin_service.create_admin(payload)
    return general.StandardResponse(
        successful="success",
        data=admin
    )

@router.patch(
    "/force/verify",
    status_code=202,
    response_model=general.StandardResponse,
    summary="Force Verify tenants",
    description="Forces verify for a tenant",
    response_description="Standard response with tenant list and meta counts.",
    include_in_schema=True,
)
async def force_verify_tenant(
    tenant_id: int = Query(..., ge=1, description="Tenant id to force-verify."),
    permission: bool = Query(
        ...,
        description="Must be true to acknowledge and execute this irreversible override.",
    ),
    admin_service: AdminService = Depends(get_admin_service),
):
    admin = await admin_service.override_verified_tenant(tenant_id=tenant_id, permission=permission)
    return admin
@router.get(
    
    "/tenants/analytics",
    summary="Platform analytics (not implemented)",
    description="Placeholder for cross-tenant KPIs (riders, drivers, uptime). Currently returns nothing.",
    response_description="Not implemented.",
    include_in_schema=False,
)
async def tenants_summary():
    ##return the number of riders
    #return number drivers
    #return active time
    #return
    pass


@router.get(
    "/tenants/{tenant_id}",
    status_code=status.HTTP_200_OK,
    response_model=general.StandardResponse[admin.AdminTenantDetail],
    summary="Tenant detail (fully expanded)",
    description=(
        "Returns a single tenant aggregated across every related model — "
        "account, profile, stats, settings, branding, pricing, drivers, "
        "riders, vehicles, bookings, payouts, and transactions. **Admin only.**"
    ),
    response_description="Standard response with the full tenant detail.",
    include_in_schema=True,
)
async def get_tenant_detail(
    tenant_id: int = Path(..., ge=1, description="Tenant id to expand."),
    admin_service: AdminService = Depends(get_admin_service),
):
    detail = await admin_service.get_tenant_detail(tenant_id)
    return general.StandardResponse(
        message="Tenant detail retrieved successfully",
        data=detail,
    )


@router.post(
    "/tenants/{tenant_id}/stripe-reminder",
    status_code=status.HTTP_200_OK,
    response_model=general.StandardResponse,
    summary="Send Stripe account completion reminder",
    description=(
        "Generates a fresh Stripe onboarding link and emails it to the tenant so they can "
        "finish their Connect account setup. **Admin only.** Fails if the tenant has no "
        "Stripe account or has already completed onboarding."
    ),
    response_description="Standard response confirming the reminder was sent.",
    include_in_schema=True,
)
async def send_stripe_completion_reminder(
    tenant_id: int = Path(..., ge=1, description="Tenant id to remind."),
    admin_service: AdminService = Depends(get_admin_service),
):
    return await admin_service.send_stripe_completion_reminder(tenant_id)
