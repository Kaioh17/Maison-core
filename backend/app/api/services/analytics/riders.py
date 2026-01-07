import asyncio
import math
import time
from zoneinfo import ZoneInfo
from fastapi import HTTPException, status, Depends
from app.db.database import get_db
from ...core import deps
from app.models import *
from app.utils import db_error_handler
from app.utils.logging import logger
from datetime import timedelta, datetime
from sqlalchemy.exc import *
from app.schemas.booking import BookingResponse

from ..service_context import ServiceContext
from ..stripe_services.checkout import BookingCheckout
from ..email_services import drivers, tenants, riders
from ..helper_service import  *

from app.models import tenant_setting
db_exceptions = db_error_handler.DBErrorHandler

class RiderAnalyticService(ServiceContext):
    def __init__(self, db, current_user):
        
        super().__init__(db, current_user)
            
    # db_exceptions = db_error_handler.DBErrorHandler
    METER_TO_MILE =  0.000621371
    MS_TO_MPH = 2.237
    # role_to_booking_field  = {
    #     "driver": booking.Bookings.driver_id,
    #     "rider": booking.Bookings.rider_id,
    #     "tenant": booking.Bookings.tenant_id,
    #     }
    async def booking_analytics(self):
        try:
            """
            This function is used for all rider booking related aggregations
            """
            # count_sql = "select booking_status, count(*) as count_stat, sum(count(*)) over () as total_bookings from bookings where rider_id = :rider_id and tenant_id = :tenant_id group by booking_status"
            count_sql = """SELECT booking_status, COUNT(*) AS count_stat
                            FROM bookings
                            WHERE rider_id = :rider_id
                            AND tenant_id = :tenant_id
                            GROUP BY booking_status 
                            
                            UNION ALL 
                            
                            SELECT 'total' AS booking_status, COUNT(*)
                            FROM bookings
                            WHERE rider_id = :rider_id
                            AND tenant_id = :tenant_id
                            """
            count_obj = self.db.execute(text(count_sql), {"rider_id":self.rider_id, "tenant_id":self.tenant_id}).mappings().all()
            
            
            # count_obj = count_.mappings().all()
            
            aggregates = {}
            for i in range(len(count_obj)):
                booking_status = count_obj[i]['booking_status']
                count =  count_obj[i]['count_stat']
                aggregates[booking_status] = count
            # logger.debug(f"Count: {aggregate}")
            return success_resp(msg="Booking analytics successful",data = aggregates)
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)
            
def get_rider_analytics(db = Depends(get_db), current_user = Depends(deps.get_current_user)):
    return RiderAnalyticService(db = db, current_user=current_user)