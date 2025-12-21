from app.models import * 
from fastapi import HTTPException, UploadFile,status 
from app.utils.logging import logger


# table_map = {
# }

# def user_exist(db):
#     db.query()
#     return 
# 
# tenant_table = tenant.Tenants
# driver_table = driver.Drivers
# booking_table = booking.Bookings

user_table = user.Users
tenant_table = tenant.Tenants
tenant_profile = tenant.TenantProfile
tenant_stats = tenant.TenantStats
driver_table = driver.Drivers
booking_table = booking.Bookings
tenant_setting_table = tenant_setting.TenantSettings  
vehicle_config_table = vehicle_config.VehicleConfig
vehicle_category_table = vehicle_category_rate.VehicleCategoryRate
vehicle_table = vehicle.Vehicles
from app.schemas import general

# class JsonResponse:
#     """  success: bool = True
#     message: Optional[str] = None
#     meta: Optional[dict] = None
#     data: Optional[T] = None"""
def success_resp(msg: str = "Successful", data: any = None, meta: dict = None):
    return general.StandardResponse(success=True, message=msg, data=data, meta=meta, error=None)
def failed_resp(msg: str = "Successful", data: any = None, meta: dict = None):
    return general.StandardResponse(success=True, message=msg, data=data, meta=meta)
def success_list_resp(msg: str = "Successful", data: any = None):
    general.ListResponse(success=True, message=msg, data=data)
class Validations:
    def __init__(self, db):
        self.db = db
        
    # @staticmethod
    def _tenant_activity_(self, tenant_id):
        tenants = self._tenants_exist(tenant_id)

        if tenants.is_active is False:
            logger.info(f"Tenant is not active right now")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail= f"Tenant {tenants.company_name} is not currently active")
        
        return tenants
    # @staticmethod
    def _tenants_exist(self, tenant_id):
        exists = self.db.query(tenant_table).filter(tenant_table.id == tenant_id).first()
        if not exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail = "Tenant does not exists")
        return exists
    
@staticmethod
def _user_exist(db, data):
    exists = db.query(user_table).filter(user_table.email == data.email, 
                                         user_table.tenant_id == data.tenant_id).first()  
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail= f"User with {data.email} already exists")





import os
@staticmethod
#this is used to verify uploads from clients and direct to respective directory or s3 bucket 
async def _verify_upload(logo_url,slug: str, upload_dir: str, file_path: str):
    if logo_url:
        try:
            contents = await logo_url.read()
            # Extract filename from the uploaded file
            filename = logo_url.filename if hasattr(logo_url, 'filename') else 'image.jpg'
            os.makedirs(upload_dir, exist_ok=True)
            _file_path = f"{file_path}_{filename}"
            with open(_file_path, "wb") as f:
                f.write(contents)
            logger.info(f"{_file_path}")
            logger.info(f"{slug}, image is saved!!")
            return file_path
        except Exception as e:
            logger.warning(f"Failed to save logo upload: {e}")
            # Continue without failing the tenant creation
    return None

from app.upload.storage.supa_s3 import supabase as supa

class SupaS3:
    async def _format_file_path(url, slug, vehicle_name: str =None, img_type:str=None):
         # Extract filename from the uploaded file
        filename = url.filename if hasattr(url, 'filename') else 'image.jpg'
        # os.makedirs(upload_dir, exist_ok=True)
        if vehicle_name:
            _file_path = f"{slug}/{vehicle_name.upper()}/{img_type}/{slug}_{filename}"
        else:
            _file_path = f"{slug}/{slug}_{filename}"
        logger.debug(_file_path)
        return _file_path
    async def upload_to_s3(url:UploadFile,slug: str, bucket_name: str, vehicle_name:str = None, img_type: str = None):
        """
        Upload a file to Supabase S3 storage bucket.
        Args:
            url (UploadFile): The file to upload.
            slug (str): Identifier slug for organizing file path.
            bucket_name (str): Target Supabase storage bucket name.
            vehicle_name (str, optional): Vehicle identifier for file organization. Defaults to None.
            img_type (str, optional): Image type/category for file organization. Defaults to None.
        Returns:
            str: Public URL of the uploaded file.
        Raises:
            Exception: If file upload fails or Supabase operation encounters an error.
        Note:
            Creates the bucket if it doesn't exist. Bucket is set to public with 5MB file size limit.
        """
      
        try:
            contents = await url.read()

            try:
                supa.storage.get_bucket(id = bucket_name)
            except:    
                logger.debug(f"Bucket not available creating new bucket:")
                supa.storage.create_bucket(
                    bucket_name,
                    options={"public": True, "file_size_limit":'5MB'}
                    )

            logger.debug(f"Starting s3 upload for url {url.filename} of size {url.size} to {bucket_name}")
            
            _file_path = await SupaS3._format_file_path(url=url,slug=slug, vehicle_name=vehicle_name, img_type=img_type)

            supa.storage.from_(bucket_name).upload(path=_file_path, file=contents, file_options={'upsert':'true'})
            logger.debug("Upload successfull")
            public_url = supa.storage.from_(bucket_name).get_public_url(_file_path)
            
            logger.debug(public_url)
            return public_url
        except Exception as e:
            raise e
    

"""
validate ids
check if user exist 
handle errors:
    ensure right user is logged in 
"""