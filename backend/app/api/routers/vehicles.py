from typing import Optional
from fastapi import APIRouter, File, HTTPException, FastAPI, Response, UploadFile,status
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from ..services import vehicle_service
from app.schemas import vehicle, vehicle_config
from ..core import deps
from .dependencies import tenant_and_driver_check, is_tenants
from app.utils.logging import logger
from typing import Optional
from app.models import vehicle_category_rate

router = APIRouter(
    prefix = "/api/v1/vehicles",
    tags = ["vehicles"]
)


@router.get("/", status_code=200, response_model=list[vehicle.VehicleResponse])
async def get_all_vehicles(is_tenants: int = Depends(is_tenants),current_user = Depends(deps.get_current_user),
                     db: Session = Depends(get_db)):
    vehicles =await vehicle_service.get_vehicles(current_user, db)
    return vehicles

@router.post("/add", status_code=status.HTTP_201_CREATED, response_model=vehicle.VehicleResponse )
async def get_all_vehicles( payload: vehicle.VehicleCreate,
                     current_user = Depends(deps.get_current_user),
                     db: Session = Depends(get_db)
                     ):
    vehicles = await vehicle_service.add_vehicle(payload, current_user, db)
    return vehicles

@router.patch("/set_rates", status_code= status.HTTP_201_CREATED, response_model=vehicle_config.VehicleCategoryRateResponse)
async def set_vehicle_flat_rate(payload: vehicle_config.VehicleRate, 
                                is_tenants: int = Depends(is_tenants),
                                current_user = Depends(deps.get_current_user),
                                db: Session = Depends(get_db)):
    vehicle_rate = await vehicle_service.set_vehicle_flat_rate(db, payload, current_user)
    return vehicle_rate

@router.get("/category", status_code= status.HTTP_200_OK, response_model=list[vehicle_config.VehicleCategoryRateResponse])
async def get_vehicle_flat_rate(is_tenants: int = Depends(is_tenants),current_user = Depends(deps.get_current_user),
                     db: Session = Depends(get_db)):
    vehicle_category = db.query(vehicle_category_rate.VehicleCategoryRate).filter(vehicle_category_rate.VehicleCategoryRate.tenant_id == current_user.id).all()
    return vehicle_category

@router.post("/create_category", status_code=status.HTTP_201_CREATED, response_model=vehicle_config.VehicleCategoryRateResponse )
async def get_all_vehicles( payload: vehicle_config.VehicleRate,
                            is_tenant = Depends(is_tenants),
                            current_user = Depends(deps.get_current_user),
                            db: Session = Depends(get_db)
                     ):
    vehicles = await vehicle_service.add_vehicle_category(payload, current_user, db)
    return vehicles

#should only be used as a form attached to "vehcile/add"
#parameters should automaticaly be filled by the frontend during update prcess
@router.patch("/add/image/{vehicle_make}/{vehicle_model}", status_code=status.HTTP_202_ACCEPTED)
async def update_vehicle_image (vehicle_make: Optional[str],vehicle_model: Optional[str],
                                vehicle_image: Optional[UploadFile] = File(None), 
                                db: Session = Depends(get_db),  
                                current_user = Depends(deps.get_current_user)
                                ):
    update_vehicle_image = await vehicle_service.update_vehicle_image(vehicle_model,vehicle_make,vehicle_image, db, current_user)
    return update_vehicle_image

# ##search fpr vehicles 
#filter by name
#filter by seat capacity 
#filter by year
#filter by category
# @router.get("/{vehicle_name}", status_code=status.HTTP_200_OK, response_model=vehicle_config.VehicleConfigResponse)
# async def search_vehicle(vehicle_name: str,
#                          db: Session = Depends(get_db), 
#                          current_user = Depends(deps.get_current_user)):
#     get_vehicle_ = await 