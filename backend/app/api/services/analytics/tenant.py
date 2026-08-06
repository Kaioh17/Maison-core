




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
from app.policies.plan_policy import PlanPolicy

from app.models import tenant_setting
db_exceptions = db_error_handler.DBErrorHandler

class TenantAnalyticService(ServiceContext):
    def __init__(self, db, current_user):
        
        super().__init__(db, current_user)
            
    # db_exceptions = db_error_handler.DBErrorHandler
    METER_TO_MILE =  0.000621371
    MS_TO_MPH = 2.237
    async def analytics(self):
        try:
            """
            This function is used for all rider booking related aggregations
            """
            # A booking counts as "billable" — and so contributes to revenue and to
            # ride volume — unless it was cancelled. Every revenue figure and both
            # 7-day series below use this same predicate so the KPI tiles, the bar
            # chart and the sparkline on the tenant Overview page always agree.
            count_sql = """SELECT
                            (
                                SELECT COUNT(*)
                                FROM bookings
                                WHERE tenant_id = :tenant_id
                                AND booking_status = 'completed'
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
                            ) AS available_drivers,
                            (
                                SELECT COALESCE(SUM(estimated_price), 0)
                                FROM bookings
                                WHERE tenant_id = :tenant_id
                                AND booking_status <> 'cancelled'
                            ) AS total_revenue,
                            (select count(id) from drivers where tenant_id = :tenant_id) as total_drivers
                            ,(select count(id) from vehicles where tenant_id = :tenant_id) as total_vehicles,
                            (select count(id) from bookings where tenant_id = :tenant_id) as total_bookings,
                            (
                                SELECT COALESCE(SUM(estimated_price), 0)
                                FROM bookings
                                WHERE tenant_id = :tenant_id
                                AND booking_status <> 'cancelled'
                                AND created_on >= DATE_TRUNC('day', NOW())
                            ) AS todays_revenue
                            """
            count_obj = self.db.execute(text(count_sql), {"tenant_id":self.tenant_id}).mappings().one()

            can_view = PlanPolicy.can_view_analytics(self.plan, self.sub_status)

            rev_rows = []
            vol_rows = []
            if can_view:
                rev_sql = """
                    SELECT to_char(day, 'Dy') AS date, COALESCE(rev, 0.0) AS revenue
                    FROM generate_series(
                        (NOW() AT TIME ZONE 'UTC')::date - INTERVAL '6 days',
                        (NOW() AT TIME ZONE 'UTC')::date,
                        '1 day'::interval
                    ) AS day
                    LEFT JOIN (
                        SELECT DATE_TRUNC('day', created_on AT TIME ZONE 'UTC')::date AS d,
                               SUM(estimated_price) AS rev
                        FROM bookings
                        WHERE tenant_id = :tenant_id
                          AND booking_status <> 'cancelled'
                          AND created_on >= DATE_TRUNC('day', NOW() AT TIME ZONE 'UTC') - INTERVAL '6 days'
                        GROUP BY d
                    ) agg ON agg.d = day
                    ORDER BY day
                """
                rev_rows = self.db.execute(text(rev_sql), {"tenant_id": self.tenant_id}).mappings().all()

                vol_sql = """
                    SELECT to_char(day, 'Dy') AS date, COALESCE(cnt, 0)::int AS count
                    FROM generate_series(
                        (NOW() AT TIME ZONE 'UTC')::date - INTERVAL '6 days',
                        (NOW() AT TIME ZONE 'UTC')::date,
                        '1 day'::interval
                    ) AS day
                    LEFT JOIN (
                        SELECT DATE_TRUNC('day', created_on AT TIME ZONE 'UTC')::date AS d,
                               COUNT(*) AS cnt
                        FROM bookings
                        WHERE tenant_id = :tenant_id
                          AND booking_status <> 'cancelled'
                          AND created_on >= DATE_TRUNC('day', NOW() AT TIME ZONE 'UTC') - INTERVAL '6 days'
                        GROUP BY d
                    ) agg ON agg.d = day
                    ORDER BY day
                """
                vol_rows = self.db.execute(text(vol_sql), {"tenant_id": self.tenant_id}).mappings().all()

            result = dict(count_obj)
            result['analytics_locked'] = not can_view
            result['revenue_last_7_days'] = [dict(r) for r in rev_rows] if can_view else None
            result['ride_volume_last_7_days'] = [dict(r) for r in vol_rows] if can_view else None

            return success_resp(msg="Retrieved analytics successful", data=result)
        except db_exceptions.COMMON_DB_ERRORS as e:
            db_exceptions.handle(e, self.db)
            
def get_tenant_analytics(db = Depends(get_db), current_user = Depends(deps.get_current_user)):
    return TenantAnalyticService(db = db, current_user=current_user)