from fastapi import APIRouter, HTTPException, FastAPI, Response,status
from fastapi.params import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from ..services import vehicle_service
from app.schemas import vehicle
from ..core import oauth2
from .dependencies import tenant_and_driver_check
from app.utils.logging import logger

router = APIRouter(
    prefix = "/api/v1/vehicles",
    tags = ["vehicles"]
)


@router.get("/", status_code=200, response_model=list[vehicle.VehicleResponse])
async def get_all_vehicles(current_user = Depends(oauth2.get_current_user),
                     db: Session = Depends(get_db)):
    vehicles =await vehicle_service.get_vehicles(current_user, db)
    return vehicles

@router.post("/add", status_code=status.HTTP_201_CREATED, response_model=vehicle.VehicleResponse )
async def get_all_vehicles( payload: vehicle.VehicleCreate,
                     current_user = Depends(oauth2.get_current_user),
                     db: Session = Depends(get_db)
                     ):
    vehicles = await vehicle_service.add_vehicle(payload, current_user, db)
    return vehicles