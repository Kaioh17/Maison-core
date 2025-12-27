from fastapi import HTTPException, status, Depends
from app.models import vehicle,tenant, vehicle_config, vehicle_category_rate
from app.utils import db_error_handler
from app.utils.logging import logger
import json
from app.db.database import get_db, get_base_db
from ..core import deps
from pathlib import Path
from .helper_service import _verify_upload, SupaS3, tenant_profile ,vehicle_table, vehicle_config_table, vehicle_category_table, success_resp
from typing import Optional
from sqlalchemy import column, func, select
from app.policies import plan_policy
from app.domain import plans
from .service_context import ServiceContext
db_exceptions = db_error_handler.DBErrorHandler


class VehicleService(ServiceContext):
    def __init__(self, db, current_user):
        super().__init__(db, current_user)
            
   
    async def update_vehicle_image(self, vehicle_id: int ,**kwargs):
        """
        Updates the vehicle images for a specified vehicle.
        This asynchronous method uploads new images for a vehicle identified by its ID. 
        It checks if the vehicle exists and validates the image types against the allowed types 
        for the vehicle's category. If the image types are valid, the images are uploaded to S3, 
        and the vehicle's image data is updated in the database.
        Parameters:
            vehicle_id (int): The ID of the vehicle to update.
            **kwargs: Additional keyword arguments that must include:
                - vehicle_image (list): A list of image URLs to be uploaded.
                - image_type (list): A list of corresponding image types for the images.
        Raises:
            HTTPException: If the vehicle is not found (404) or if an unsupported image type is provided (400).
        Returns:
            dict: A success response containing a message and the updated image URLs.
        """
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
           
            vehicle_name = vehicle.vehicle_name
            logger.debug(f"Vehicle_name: {vehicle_name}")
        
            vehicle_image = kwargs['vehicle_image']
            logger.debug(vehicle_image)
            image_type = kwargs['image_type']
            
            
            current_types = []
            current_urls = []
            file_urls =[]
            if vehicle.vehicle_images:                
                response:dict = vehicle.vehicle_images
                for k, v in response.items():
                    current_types.append(k)
                    current_urls.append(v)
                
                logger.debug(f"Vehicle saved images {current_types} {current_urls} {response}")
            else: 
                response = {}
            for i,image in enumerate(vehicle_image):
                get_type = image_type[i].lower()
                
                ##Delete images going to existing file
                if get_type in current_types:
                    logger.debug(f"Deleting previous: {get_type}")
                    idx = current_types.index(get_type)
                    url = current_urls[idx]
                    file_parts = url.split('public/')[1].split('/',1)
                    logger.debug(f"File parts: {file_parts}")
                    
                    bucket_name = file_parts[0]
                    file_url = file_parts[1]
                    file_urls.append(file_url)
                    
                    await SupaS3.delete_from_s3(bucket_name=bucket_name, file_urls=file_urls)
                if get_type not in allowed_types:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Image type '{get_type}' is not supported. Allowed types: {', '.join(allowed_types)}")
                image_url = await SupaS3.upload_to_s3(url=image, slug=slug, bucket_name="vehicles", vehicle_name=vehicle_name, img_type=get_type, vehicle_id=vehicle_id)
                if image_url:
                    response[get_type] = image_url
               
                        
            logger.debug(f"new images{response}")
            vehicle.vehicle_images = response
            
            self.db.commit()
            # self.db.refersh(vehicle)
            logger.debug(f"After commit {vehicle.vehicle_images}")
            
            return success_resp(msg="Updated image successfully", meta={"image_types": image_type}, data=response)

        except Exception as e:
            logger.error(f"There is an unexpected error {e}")
            raise e
    async def get_vehicles(self, vehicle_id: int =None, driver_id: int =None):
        try:
            logger.debug("Self.role")
            add ="."
            if vehicle_id and self.role != 'driver':
                vehicles = self.db.query(vehicle_table).filter(vehicle_table.tenant_id == self.tenant_id,vehicle_table.id == vehicle_id).all()
                add=f", with Vehicle [{vehicle_id}]"
                
            elif self.role == "driver":
                vehicles = self.db.query(vehicle_table).filter(vehicle_table.tenant_id == self.tenant_id,vehicle_table.driver_id == self.driver_id).all()
                add = f". For driver [{self.driver_id}]"
            elif driver_id:
                vehicles = self.db.query(vehicle_table).filter(vehicle_table.tenant_id == self.tenant_id,vehicle_table.driver_id == driver_id).all()
                add=f". For driver [{driver_id}]"
            else:
                vehicles = self.db.query(vehicle_table).filter(vehicle_table.tenant_id == self.tenant_id).all()
                add=f". For tenant [{self.tenant_id}]"

            if not vehicles:
                logger.debug(f"There are no vehicles{add}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail = f"There are no vehicles{add}")
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)
        return success_resp(msg="Retrieved successfully", meta=None, data=vehicles)

    async def get_category(self, tenant_id):
        vehicle_category = self.db.query(vehicle_category_rate.VehicleCategoryRate).filter(vehicle_category_rate.VehicleCategoryRate.tenant_id == tenant_id).all()
        return success_resp(msg="Retrieved successfully", meta=None, data=vehicle_category)
        
        # return vehicle_category
    async def get_allowed_image_types(self):
        vehicle_category = self.db.query(vehicle_category_rate.VehicleCategoryRate).filter(vehicle_category_rate.VehicleCategoryRate.tenant_id == self.tenant_id).first()
        return success_resp(msg="Retrieved successfully", meta=None, data=vehicle_category)
    def _count_vehicles(self, tenant_id):
        try:
            stmt = select(func.count()).where(vehicle_table.tenant_id == tenant_id)
            count = self.db.scalar(stmt)
            
            return count
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)
            
    async def add_vehicle(self, payload):
        
        try:
            # profile_response:tenant_profile =self.db.query(tenant_profile).filter(tenant_profile.tenant_id == self.tenant_id).first()
            # print(f"Profile {profile_response.subscription_plan}")
            current_vehicle_count = self._count_vehicles(self.tenant_id)
            
            #set policy             
            plan = plans.PLAN_REGISTRY[self.sub_plan]
            logger.debug(f"Name {plan}")
            plan_policy.PlanPolicy.can_create_vehicle(plan=plan, current_vehicle_count=current_vehicle_count)
            
            tenants = self.db.query(tenant.Tenants).filter(tenant.Tenants.id == self.current_user.id).first()#for drivers TODO -> switch to a dependency injection
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
    """Delete vehcicles by vehicle_id"""
    async def delete_vehicle(self, vehcile_id, approve_delete: bool = False):
        resp = self.db.query(vehicle_table).filter(vehicle_table.id == vehcile_id,
                                            vehicle_table.tenant_id == self.tenant_id).first()
        if not resp:
            logger.warning("Vehicle does not exist to delete")
            raise HTTPException(status_code=404,
                                    detail="Vehicle does not exist to delete")
        if resp.driver_id and approve_delete != True:
            logger.warning("Cannot delete vehicles with drivers")
            raise HTTPException(status_code=401,
                                    detail="Cannot delete vehicles with drivers")
        files:dict = resp.vehicle_images
        logger.debug(f"Vehicles: {files}")
        file_urls = []
        if files is not None:
            for k, v in files.items():
                v:str
                file_parts = v.split('public/')[1].split('/',1)
                logger.debug(f"File parts: {file_parts}")
                
                bucket_name = file_parts[0]
                file_url = file_parts[1]
                file_urls.append(file_url)
                
                logger.debug(f"Bucket_name: {bucket_name}, file_url: {file_urls}")
                
                
                # file_url = 
            
            await SupaS3.delete_from_s3(bucket_name, file_urls)
        self.db.delete(resp)
        self.db.commit()
        return
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
def get_unauthorized_vehicle_service(db = Depends(get_base_db)):
    return VehicleService(db=db, current_user=None)  



