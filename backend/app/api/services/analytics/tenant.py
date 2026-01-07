




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

class TenantAnalyticService(ServiceContext):
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
    async def analytics(self):
        try:
            """
            This function is used for all rider booking related aggregations
            """
            # count_sql = "select booking_status, count(*) as count_stat, sum(count(*)) over () as total_bookings from bookings where rider_id = :rider_id and tenant_id = :tenant_id group by booking_status"
            count_sql = """SELECT
                            (
                                SELECT COUNT(*)
                                FROM bookings
                                WHERE tenant_id = :tenant_id
                                AND booking_status = 'confirmed'
                            ) AS completed_rides,

                            (
                                SELECT COUNT(*)
                                FROM bookings
                                WHERE tenant_id = :tenant_id
                                AND booking_status = 'pending'
                            ) AS pending_rides,

                            (
                                SELECT COUNT(*)
                                FROM drivers
                                WHERE tenant_id = :tenant_id
                                AND is_active = true
                            ) AS available_drivers, (select sum(estimated_price)  from bookings where tenant_id = :tenant_id and payment_id IS NOT NULL) as total_revenue,
                            (select count(id) from drivers where tenant_id = :tenant_id) as total_drivers
                            ,(select count(id) from vehicles where tenant_id = :tenant_id) as total_vehicles,
                            (select count(id) from bookings where tenant_id = :tenant_id) as total_bookings,
                            (select sum(estimated_price)  from bookings where tenant_id = :tenant_id and payment_id IS NOT NULL and created_on >= (SELECT (NOW() - INTERVAL '5 day') AT TIME ZONE 'UTC')) as todays_revenue
                            """
           
            count_obj = self.db.execute(text(count_sql), {"tenant_id":self.tenant_id}).mappings().one()
            
            
            # count_obj = count_.mappings().all()
            
            # aggregates = {}
            # for i in range(len(count_obj)):
            #     booking_status = count_obj[i]['booking_status']
            #     count =  count_obj[i]['count_stat']
            #     aggregates[booking_status] = count
            # logger.debug(f"Count: {count_obj}")
            return success_resp(msg="Reteieved analytics successful",data = count_obj)
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)
            
def get_tenant_analytics(db = Depends(get_db), current_user = Depends(deps.get_current_user)):
    return TenantAnalyticService(db = db, current_user=current_user)