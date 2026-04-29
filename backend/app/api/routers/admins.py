from fastapi import APIRouter, HTTPException, FastAPI, Response, status, Path
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
