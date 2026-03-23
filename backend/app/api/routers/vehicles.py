from typing import Optional
from fastapi import APIRouter, File, Form, UploadFile, status, Path
from fastapi.params import Depends
from ..services.vehicle_service import (
    VehicleService,
    get_unauthorized_vehicle_service,
    get_vehicle_service,
)
from app.schemas import vehicle, vehicle_config
from app.schemas.general import StandardResponse as resp
from .dependencies import is_tenants
from app.utils.logging import logger
router = APIRouter(
    prefix="/api/v1/vehicles",
    tags=["vehicles"],
)


@router.get(
    "/",
    status_code=200,
    response_model=resp[list[vehicle.VehicleResponse]],
    summary="List vehicles (tenant/driver)",
    description=(
        "Fleet list for the current tenant context. Optional **`vehicle_id`** or **`driver_id`** filters. "
        "Requires tenant or driver JWT per dependency chain."
    ),
    response_description="List of vehicles.",
)
async def list_vehicles(
    vehicle_id: Optional[int] = None,
    driver_id: Optional[int] = None,
    vehicle_service: VehicleService = Depends(get_vehicle_service),
):
    logger.debug("Vehicles...")
    vehicles = await vehicle_service.get_vehicles(
        vehicle_id=vehicle_id, driver_id=driver_id
    )
    return vehicles


@router.get(
    "/riders",
    status_code=200,
    response_model=resp[list[vehicle.VehicleResponse]],
    summary="List vehicles (rider-facing)",
    description="Simplified fleet list for booking UI (same underlying query as `/` without filters). Requires auth.",
    response_description="List of vehicles.",
)
async def list_vehicles_for_riders(
    vehicle_service: VehicleService = Depends(get_vehicle_service),
):
    vehicles = await vehicle_service.get_vehicles()
    return vehicles


@router.get(
    "/image/types",
    status_code=200,
    response_model=resp[vehicle.ImageTypes],
    summary="Allowed vehicle image slot names",
    description="Returns configured image type keys (exterior, interior, etc.) for uploads.",
    response_description="Image type schema.",
)
async def get_vehicle_image_types(
    vehicle_service: VehicleService = Depends(get_vehicle_service),
):
    vehicles = await vehicle_service.get_allowed_image_types()
    return vehicles


@router.post(
    "/add",
    status_code=status.HTTP_201_CREATED,
    response_model=resp[vehicle.VehicleResponse],
    summary="Add a vehicle to the fleet",
    description="Creates a vehicle for the tenant; ties to category/rates as configured. Requires tenant JWT.",
    response_description="Created vehicle.",
)
async def add_vehicle(
    payload: vehicle.VehicleCreate,
    vehicle_service: VehicleService = Depends(get_vehicle_service),
):
    vehicles = await vehicle_service.add_vehicle(payload)
    return vehicles


@router.patch(
    "/set_rates",
    status_code=status.HTTP_201_CREATED,
    response_model=resp[vehicle_config.VehicleCategoryRateResponse],
    summary="Set flat rate for a vehicle category",
    description="Updates **`VehicleCategoryRate`** for the tenant. Requires **tenant** JWT.",
    response_description="Updated category rate row.",
)
async def set_vehicle_flat_rate(
    payload: vehicle_config.VehicleRate,
    is_tenants: int = Depends(is_tenants),
    vehicle_service: VehicleService = Depends(get_vehicle_service),
):
    vehicle_rate = await vehicle_service.set_vehicle_flat_rate(payload)
    return vehicle_rate


@router.get(
    "/category/{tenant_id}",
    status_code=status.HTTP_200_OK,
    response_model=resp[list[vehicle_config.VehicleCategoryRateResponse]],
    summary="Public: vehicle categories for a tenant",
    description=(
        "Unauthenticated lookup of vehicle categories and rates for **`tenant_id`** "
        "(e.g. booking flow before login)."
    ),
    response_description="List of category rate rows.",
)
async def get_vehicle_categories_public(
    tenant_id: int = Path(..., description="Tenant primary key."),
    vehicle_service: VehicleService = Depends(get_unauthorized_vehicle_service),
):
    vehicle_category = await vehicle_service.get_category(tenant_id)
    return vehicle_category


@router.post(
    "/create_category",
    status_code=status.HTTP_201_CREATED,
    response_model=resp[vehicle_config.VehicleCategoryRateResponse],
    summary="Create a vehicle category / rate row",
    description="Adds a new category (sedan, SUV, …) with flat rate for pricing. Requires **tenant** JWT.",
    response_description="Created category rate.",
)
async def create_vehicle_category(
    payload: vehicle_config.VehicleRate,
    is_tenant=Depends(is_tenants),
    vehicle_service: VehicleService = Depends(get_vehicle_service),
):
    vehicles = await vehicle_service.add_vehicle_category(payload)
    return vehicles


@router.patch(
    "/add/image/{vehicle_id}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=resp[dict],
    summary="Upload vehicle images",
    description=(
        "Multipart upload: **`image_type`** form fields align with **`vehicle_image`** files. "
        "Updates JSON image map on the vehicle. Requires tenant JWT."
    ),
    response_description="Upload result / URLs.",
)
async def update_vehicle_image(
    vehicle_id: int = Path(..., description="Vehicle id."),
    image_type: list[str] = Form(
        description="Parallel labels for each file (e.g. front_exterior)."
    ),
    vehicle_image: Optional[list[UploadFile]] = File(None),
    vehicle_service: VehicleService = Depends(get_vehicle_service),
):
    update_vehicle_image = await vehicle_service.update_vehicle_image(
        vehicle_id=vehicle_id,
        vehicle_image=vehicle_image,
        image_type=image_type,
    )
    return update_vehicle_image


@router.delete(
    "/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a vehicle",
    description="Removes a vehicle; **`approve_delete`** may gate destructive action. Requires **tenant** JWT.",
    response_description="No content on success.",
)
async def delete_vehicle(
    vehicle_id: int = Path(..., description="Vehicle id."),
    approve_delete: bool = False,
    is_tenant=Depends(is_tenants),
    vehicle_service: VehicleService = Depends(get_vehicle_service),
):
    delete_vehicle = await vehicle_service.delete_vehicle(
        vehicle_id, approve_delete=approve_delete
    )
    return delete_vehicle
