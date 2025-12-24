from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, FastAPI, Response, UploadFile,status
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
# from ..services import vehicle_service
from ..services.vehicle_service import VehicleService, get_unauthorized_vehicle_service, get_vehicle_service
from app.schemas import vehicle, vehicle_config
from app.schemas.general import StandardResponse as resp
from ..core import deps
from .dependencies import tenant_and_driver_check, is_tenants
from app.utils.logging import logger
from typing import Optional
from app.models import vehicle_category_rate

router = APIRouter(
    prefix = "/api/v1/vehicles",
    tags = ["vehicles"]
)


@router.get("/", status_code=200, response_model=resp[list[vehicle.VehicleResponse]])
async def get_all_vehicles(vehicle_id: Optional[int] = None,
                           vehicle_service: VehicleService = Depends(get_vehicle_service),
                           ):
    vehicles =await vehicle_service.get_vehicles(vehicle_id)
    return vehicles


@router.get("/riders", status_code=200, response_model=resp[list[vehicle.VehicleResponse]])
async def get_all_vehicles(vehicle_service: VehicleService = Depends(get_vehicle_service),
                           ):
    vehicles=await vehicle_service.get_vehicles()
    return vehicles
@router.get("/image/types", status_code=200, response_model=resp[vehicle.ImageTypes])
async def get_all_vehicles(vehicle_service: VehicleService = Depends(get_vehicle_service),
                           ):
    vehicles =await vehicle_service.get_allowed_image_types()
    return vehicles
@router.post("/add", status_code=status.HTTP_201_CREATED, response_model=resp[vehicle.VehicleResponse] )
async def add_vehicles( payload: vehicle.VehicleCreate,
                            vehicle_service: VehicleService = Depends(get_vehicle_service),
                           
                    
                     ):
    vehicles = await vehicle_service.add_vehicle(payload)
    return vehicles


@router.patch("/set_rates", status_code= status.HTTP_201_CREATED, response_model=resp[vehicle_config.VehicleCategoryRateResponse])
async def set_vehicle_flat_rate(payload: vehicle_config.VehicleRate, 
                                is_tenants: int = Depends(is_tenants),
                                vehicle_service: VehicleService = Depends(get_vehicle_service),
                                
                                ):
    vehicle_rate = await vehicle_service.set_vehicle_flat_rate(payload)
    return vehicle_rate

@router.get("/category", status_code= status.HTTP_200_OK, response_model=resp[list[vehicle_config.VehicleCategoryRateResponse]])
async def get_vehicle_flat_rate(vehicle_service: VehicleService = Depends(get_vehicle_service)):
    
    vehicle_category =await vehicle_service.get_category()
    return vehicle_category

@router.post("/create_category", status_code=status.HTTP_201_CREATED, response_model=resp[vehicle_config.VehicleCategoryRateResponse])
async def get_all_vehicles( payload: vehicle_config.VehicleRate,
                            is_tenant = Depends(is_tenants),
                            
                            vehicle_service: VehicleService = Depends(get_vehicle_service)
                            
                     ):
    vehicles = await vehicle_service.add_vehicle_category(payload)
    return vehicles

#should only be used as a form attached to "vehcile/add"
#parameters should automaticaly be filled by the frontend during update prcess
@router.patch("/add/image/{vehicle_id}", status_code=status.HTTP_202_ACCEPTED, response_model=resp[dict])
async def update_vehicle_image (vehicle_id: int,
                                image_type: list[str] = Form(), #[front, rare, back, ....]
                                vehicle_image: Optional[list[UploadFile]] = File(None), #[url0, url1, url2]
                                vehicle_service: VehicleService = Depends(get_vehicle_service),
                                ):    
    # return
    update_vehicle_image = await vehicle_service.update_vehicle_image(vehicle_id=vehicle_id,
                                                                      vehicle_image=vehicle_image, 
                                                                      image_type = image_type)
    return update_vehicle_image

@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(vehicle_id: int, approve_delete: bool =False,is_tenant = Depends(is_tenants),vehicle_service: VehicleService = Depends(get_vehicle_service)):
    delete_vehicle = await vehicle_service.delete_vehicle(vehicle_id, approve_delete=approve_delete)
    return delete_vehicle
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