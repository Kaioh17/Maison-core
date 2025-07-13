from fastapi import Depends, HTTPException, status
from ..core import oauth2

# from services import helper_service
# from services import helper_service

def is_rider(current_rider = Depends(oauth2.get_current_user)):
    if current_rider.role != "rider":
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            detail = "Current user cannot book rides")
    return current_rider