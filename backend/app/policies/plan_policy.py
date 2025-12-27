from fastapi import FastAPI,  HTTPException, status
class PlanPolicyError(HTTPException):
    pass
    
    

class PlanPolicy:
    @staticmethod
    def can_create_vehicle(plan, current_vehicle_count):
        if current_vehicle_count >= plan.max_vehicle:
            raise PlanPolicyError(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"Cannot add {current_vehicle_count +1 }. Already reached max vehicle count of {plan.max_vehicle}")
    # @staticmethod
    # def assert_can_create_vehicle(plan, current_vehicle_count: int):
        # if current
    @staticmethod
    def can_add_driver(plan, current_driver_count):
        if current_driver_count >= plan.max_driver_count:
            raise PlanPolicyError(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"Cannot add {current_driver_count+1}. Already reached max driver count of {plan.max_vehicle}")
            
    @staticmethod
    def assert_can_upload_images(plan, current_image_count: int, 
                                 images_to_add: int):
        if current_image_count + images_to_add > plan.max_images_per_vehicle:
            raise PlanPolicyError(detail="Cannot add ve")