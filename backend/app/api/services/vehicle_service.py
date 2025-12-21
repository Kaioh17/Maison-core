from fastapi import HTTPException, status, Depends
from app.models import vehicle,tenant, vehicle_config, vehicle_category_rate
from app.utils import db_error_handler
from app.utils.logging import logger
import json
from app.db.database import get_db, get_base_db
from ..core import deps
from pathlib import Path
from .helper_service import _verify_upload, SupaS3, vehicle_table, vehicle_config_table, vehicle_category_table, success_resp
from typing import Optional
db_exceptions = db_error_handler.DBErrorHandler


class VehicleService:
    def __init__(self, db, current_user):
        self.db = db
        self.current_user = current_user
        self.role = self.current_user.role.lower()
        if self.role in ['driver','rider']:
           self.tenant_id = self.current_user.tenant_id
        else:
            self.tenant_id = self.current_user.id
            # self.slug = self.current_user.slug
            
            
   
    async def update_vehicle_image(self, vehicle_id: int ,**kwargs):
        try:             
            
            vehicle = self.db.query(vehicle_table).filter(vehicle_table.tenant_id == self.tenant_id ,
                                                                    vehicle_table.id == vehicle_id
                                                        ).first()
                
            slug = self.current_user.slug
            logger.debug(slug)
        
            if not vehicle:
                logger.warning(f"[Vehicle Not found] {vehicle_id} cannot be updated")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail = "vehicle does not exists")
            allowed_types = self.db.query(vehicle_category_table).filter(vehicle_table.tenant_id == self.tenant_id ,
                                                                        ).first().allowed_image_types
            logger.debug(f'allowed_types: {allowed_types}')
            # logger.info(f"Vehicle image [{vehicle_make}-{vehicle_model}] has been updated")
            upload_dir = f"app/upload/vehicle_image"
            vehicle_name = vehicle.vehicle_name
            logger.debug(f"Vehicle_name: {vehicle_name}")
            # logger.debug(f"Vehicle_image: {vehicle_image}")
            # logger.debug(f"Vehicle_image: {vehicle_image.vehicle_image}")
            vehicle_image = kwargs['vehicle_image']
            logger.debug(vehicle_image)
            image_type = kwargs['image_type']
            
            response = {}
            for i,image in enumerate(vehicle_image):
                get_type = image_type[i].lower()
                if get_type not in allowed_types:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Image type '{get_type}' is not supported. Allowed types: {', '.join(allowed_types)}")
                image_url = await SupaS3.upload_to_s3(url=image, slug=slug, bucket_name="vehicles", vehicle_name=vehicle_name, img_type=get_type)
                if image_url:
                    response[get_type] = image_url
        
            
            logger.debug(f"{response}")
            vehicle.vehicle_images = response
            self.db.commit()
            return success_resp(msg="Updated image successfully", meta={"image_types": image_type}, data=response)
            return {"msg": response}
        except Exception as e:
            logger.error(f"There is an unexpected error {e}")
            raise e
    async def get_vehicles(self):
        try:
           
            vehicles = self.db.query(vehicle.Vehicles).filter(vehicle.Vehicles.tenant_id == self.tenant_id).all()

            if not vehicles:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail = "There are no vehicles")
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)
        return success_resp(msg="Retrieved successfully", meta=None, data=vehicles)

    async def get_category(self):
        vehicle_category = self.db.query(vehicle_category_rate.VehicleCategoryRate).filter(vehicle_category_rate.VehicleCategoryRate.tenant_id == self.tenant_id).all()
        return success_resp(msg="Retrieved successfully", meta=None, data=vehicle_category)
        
        # return vehicle_category

        
    async def add_vehicle(self, payload):
        try:
            tenants = self.db.query(tenant.Tenants).filter(tenant.Tenants.id == self.current_user.id).first()
            if not tenants:
                raise HTTPException(status_code=404, detail="Tenants not found")
            
            vehicle_exists = self.db.query(vehicle.Vehicles).filter(vehicle.Vehicles.license_plate == payload.license_plate).first()
            if vehicle_exists:
                logger.warning("Vehicle with license plate already exists")
                raise HTTPException(status_code=409,
                                    detail="Vehicle with liscence plate alredy present")
            logger.info("Creating vehicle...")

            vehicle_info = payload.model_dump()
            
            # config = payload.vehicle_category_id 
            tenant_id = self.current_user.id
            if self.current_user.role != "tenant":
                tenant_id = self.current_user.tenant_id

            # vehicle_category_ = db.query(vehicle_category_table).filter(vehicle_category_table.tenant_id == user,
            #                                                             vehicle_category_table.id == config).first()
            
            get_category_id = self._get_category(payload.vehicle_category,tenant_id= tenant_id)
            
            vehicle_info.pop("vehicle_category", None) #except vehicle category
            new_vehicle = vehicle.Vehicles(tenant_id=tenant_id,vehicle_category_id = get_category_id ,**vehicle_info)
            # new_vehicle_config = vehicle_config_table(tenant_id=tenant_id,vehicle_category = vehicle_category_id, )

        
            self.db.add(new_vehicle)
            self.db.commit()
            self.db.refresh(new_vehicle)
            # logger.info(f"{payload.make} added to {tenants.company}..")
            return success_resp(msg="Added Vehicle successfully", meta=None, data=new_vehicle)
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)

       

    def _get_category(self, vehicle_category,tenant_id):
        try:
            
            vehicle_category_ = self.db.query(vehicle_category_table).filter(vehicle_category_table.tenant_id == tenant_id,
                                                                        vehicle_category_table.vehicle_category== vehicle_category).first()
            
            if not vehicle_category_:
                raise HTTPException(status_code=400,detail="The vehicle category does not exists")
            logger.info(f"Vehicle_category: {vehicle_category_.id}")
            return  vehicle_category_.id
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)
            
            
    def load_vehicles(self):
        try:
            vehicle_data = None
            
            path =Path(__file__).parent.parent.parent/ "data"/ "vehicles.json"

            if not path.exists():
                logger.error(f"Vehicle data file not found at  {path}")
                raise HTTPException(status_code=500,
                                    detail="Vehicle configuration file is missing")
            
            with open(path, "r") as f:
                vehicle_data = json.load(f)
            
            if not vehicle_data:
                logger.error("Vehicle data file is empty")
                raise HTTPException(status_code=500,
                                    detail="Vehicle configuration is empty")
            logger.info("Vehic;e data loaded success fully")
            return vehicle_data
            # return success_resp(msg="Updated image successfully", meta=None, data=vehicle_data)
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in vehicle data file: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Invalid vehicle configuration format")
        except IOError as e:
            logger.error(f"Error reading vehicle data file: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error reading vehicle configuration") 
        

    async def add_vehicle_category(self, payload ):
        try:
            logger.info(f"[{self.current_user.id}] add new vehicle category...")
            category_info = payload.model_dump()
            vehicle_category = vehicle_category_table(tenant_id = self.current_user.id, **category_info)

            self.db.add(vehicle_category)
            self.db.commit()
            self.db.refresh(vehicle_category)
            return success_resp(msg="Updated image successfully", meta=None, data=vehicle_category)
            
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)

    """Update vehicle flat rate """
    async def set_vehicle_flat_rate(self, payload):
        try:
            category_ = self.db.query(vehicle_category_table).filter(vehicle_category_table.tenant_id == self.current_user.id,
                                                                vehicle_category_table.vehicle_category == payload.vehicle_category).first()
            config_ = self.db.query(vehicle_config_table).filter(vehicle_config_table.tenant_id == self.current_user.id,
                                                            vehicle_config_table.vehicle_category == payload.vehicle_category).all()

            if config_:
                for v in config_:
                    v.vehicle_flat_rate = payload.vehicle_flat_rate
            
            if not category_:
                raise HTTPException(status_code=404, detail= f"There is no vehicle catgory for tenant {self.current_user.id}")
            
            if payload.vehicle_flat_rate < 0:
                logger.warning("Flat rate entered is lower than 0")
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                                detail=f"Vehicle flat rate cannot be lower than 0")
            category_.vehicle_flat_rate = payload.vehicle_flat_rate

            self.db.commit()
            self.db.refresh(category_)
            return success_resp(msg="Updated image successfully", meta=None, data=category_)
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)
def get_vehicle_service(db = Depends(get_db),current_user=Depends(deps.get_current_user)):
    return VehicleService(db=db, current_user=current_user)
def get_unauthorized_vehicle_service(db = Depends(get_db)):
    return VehicleService(db=db, current_user=None)  



