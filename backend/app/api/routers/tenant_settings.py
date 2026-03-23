from fastapi import APIRouter, status, UploadFile, File
from fastapi.params import Depends
from ..services.tenant_settings_service import get_tenant_setting_service, TenantSettingsService
from app.schemas import tenant_setting, general
from app.utils.logging import logger
from typing import Optional


router = APIRouter(
    prefix="/api/v1/tenant/config",
    tags=["Tenant Config"],
)


@router.get(
    "/{config_type}",
    status_code=status.HTTP_200_OK,
    response_model=general.StandardResponse[tenant_setting.TenantConfigResponse],
    summary="Get tenant configuration slice",
    description=(
        "Fetch settings, pricing, branding, booking deposit rows, or **`all`** aggregates. "
        "Path **`config_type`**: `setting` | `pricing` | `branding` | `booking` | `all` (enum). "
        "Requires **tenant** JWT."
    ),
    response_description="Config object or combined `TenantConfigResponse`.",
)
async def get_tenant_settings(
    config_type: Optional[tenant_setting.ConfigTypes] = None,
    tenant_settings_service: TenantSettingsService = Depends(get_tenant_setting_service),
):
    logger.info("Getting tenant settings")
    tenant_setting_obj = await tenant_settings_service.get_tenant_settings(
        config_type=config_type
    )
    return tenant_setting_obj


@router.patch(
    "/settings",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=general.StandardResponse[tenant_setting.UpdateTenantSetting],
    summary="Update core tenant settings JSON",
    description="Patches **`rider_tiers_enabled`** and/or nested **`config`** (booking, branding, features). Requires **tenant** JWT.",
    response_description="Updated settings row.",
)
async def update_tenant_settings_core(
    payload: tenant_setting.UpdateTenantSetting,
    tenant_settings_service: TenantSettingsService = Depends(get_tenant_setting_service),
):
    logger.info("Updating settings...")
    upated_tenant_setting = await tenant_settings_service.update_tenant_settings(payload)
    return upated_tenant_setting


@router.patch(
    "/pricing",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=general.StandardResponse[tenant_setting.TenantPricingPublic],
    summary="Update base pricing",
    description="Updates **`tenant_pricing`** (base fare, per mile, cancellation, etc.). Requires **tenant** JWT.",
    response_description="Updated pricing row.",
)
async def update_tenant_pricing(
    payload: tenant_setting.TenantPricingUpdate,
    tenant_settings_service: TenantSettingsService = Depends(get_tenant_setting_service),
):
    logger.info("Updating pricing config...")
    upated_tenant_setting = await tenant_settings_service.update_tenant_pricing(payload)
    return upated_tenant_setting


@router.patch(
    "/branding",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=general.StandardResponse[tenant_setting.TenantBrandingPublic],
    summary="Update branding / white-label",
    description="Theme, colors, logo URLs, email sender, slug sync to profile. Requires **tenant** JWT.",
    response_description="Updated branding row.",
)
async def update_tenant_branding_route(
    payload: tenant_setting.TenantBrandingUpdate,
    tenant_settings_service: TenantSettingsService = Depends(get_tenant_setting_service),
):
    logger.info("Updating branidng...")
    upated_tenant_setting = await tenant_settings_service.update_tenant_branding(payload)
    return upated_tenant_setting


@router.patch(
    "/logo",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=general.StandardResponse[tenant_setting.updated_visuals],
    summary="Upload logo and/or favicon",
    description="Multipart upload to object storage; updates branding + profile logo URLs. Requires **tenant** JWT.",
    response_description="New logo/favicon URLs.",
)
async def update_logo(
    tenant_settings_service: TenantSettingsService = Depends(get_tenant_setting_service),
    logo_url: Optional[UploadFile] = File(None),
    favicon_url: Optional[UploadFile] = File(None),
):
    updated_logo = await tenant_settings_service.update_logo(logo_url, favicon_url)
    return updated_logo


@router.patch(
    "/booking/{service_type}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=general.StandardResponse[tenant_setting.TenantBookingPublic],
    summary="Update per-service booking pricing",
    description=(
        "Updates **`tenant_booking_price`** for **`service_type`** (e.g. `airport`, `dropoff`, `hourly`): "
        "deposits, airport fees, etc. Requires **tenant** JWT."
    ),
    response_description="Updated booking price row.",
)
async def update_booking_prices(
    service_type: str,
    payload: tenant_setting.TenantBookingUpdate,
    tenant_settings_service: TenantSettingsService = Depends(get_tenant_setting_service),
):
    updated_logo = await tenant_settings_service.update_tenant_booking(
        service_type=service_type, payload=payload
    )
    return updated_logo


@router.delete(
    "/settings/{service_type}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove custom booking service type",
    description=(
        "Deletes a custom key from `config.booking.types` and related rows; **system** types may be forbidden. "
        "Requires **tenant** JWT."
    ),
    response_description="No content.",
)
async def delete_service_type(
    service_type: str,
    tenant_settings_service: TenantSettingsService = Depends(get_tenant_setting_service),
):
    deleted_service_type = await tenant_settings_service.delete_service_type(
        service_type=service_type
    )
    return deleted_service_type
