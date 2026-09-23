from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.config import Settings
from app.schemas import general

router = APIRouter(prefix="/api/v1/demo", tags=["Demo"])
settings = Settings()


class DemoCredentials(BaseModel):
    email: str
    password: str


@router.get(
    "/credentials/{role}",
    response_model=general.StandardResponse[DemoCredentials],
    summary="Public: demo login credentials",
    description=(
        "Returns the seeded demo account's credentials so login pages can prefill them. "
        "`tenant` is served whenever a demo is configured; `driver`/`rider` only when `slug` "
        "equals `DEMO_TENANT_SLUG`. 404 otherwise, so real tenants never reveal anything."
    ),
)
async def demo_credentials(
    role: Literal["tenant", "driver", "rider"],
    slug: Optional[str] = Query(None, description="Tenant slug from the subdomain (driver/rider only)."),
):
    email = getattr(settings, f"demo_{role}_email")
    password = getattr(settings, f"demo_{role}_password")
    allowed = bool(settings.demo_tenant_slug) and (role == "tenant" or slug == settings.demo_tenant_slug)
    if not (allowed and email and password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return general.StandardResponse(data=DemoCredentials(email=email, password=password))
