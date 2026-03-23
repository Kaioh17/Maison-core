from fastapi import APIRouter, status, Path
from fastapi.params import Depends
from ..services.slug_services import get_slug_service, SlugService, get_slug_authorized_service
from app.schemas import general, slug


router = APIRouter(
    prefix="/api/v1/slug",
    tags=["Slug"],
)


@router.get(
    "/{slug}",
    status_code=status.HTTP_200_OK,
    response_model=general.StandardResponse[slug.TenantSlugResponse],
    summary="Public: validate tenant slug",
    description=(
        "Used by signup and white-label frontends to check that a **`slug`** exists and retrieve public tenant metadata. "
        "No JWT required."
    ),
    response_description="Slug validation + tenant public fields.",
)
async def verify_slug_public(
    slug: str = Path(..., description="Tenant slug (subdomain key)."),
    slug_service: SlugService = Depends(get_slug_service),
):
    slug_ = slug_service.verify_slug(slug)
    return slug_


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=general.StandardResponse[slug.TenantSetupResponse],
    summary="Authenticated: tenant setup metadata",
    description="Returns extended setup info for the current tenant context. Requires auth (slug service dependency).",
    response_description="Tenant setup payload.",
)
async def get_tenant_setup_authenticated(
    slug_service: SlugService = Depends(get_slug_authorized_service),
):
    slug_ = slug_service.get_tenant_setup()
    return slug_
