from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

PayoutStatus = Literal["pending", "paid", "disputed", "verified"]


class PayoutRow(BaseModel):
    """One completed ride's pay line. Net movement for the ride = amount + adjustment."""
    booking_id: int
    payout_id: int
    driver_id: int
    driver_name: str
    pickup_time: datetime
    fare: float
    payment_method: Optional[str] = None
    earning: float = Field(..., description="Driver's share, frozen at completion.")
    amount: float = Field(..., description="+ company owes driver, - driver owes company (cash held).")
    adjustment: float
    status: PayoutStatus
    status_by_role: Optional[Literal["tenant", "driver"]] = None
    status_on: Optional[datetime] = None
    note: Optional[str] = None


class PayoutsResponse(BaseModel):
    configured: bool = Field(..., description="Whether the tenant has set a driver pay rule.")
    rows: list[PayoutRow]


class PayoutUpdate(BaseModel):
    status: Optional[PayoutStatus] = None
    adjustment: Optional[float] = Field(None, ge=-100000, le=100000)
    note: Optional[str] = Field(None, max_length=500)


class PayoutBulkUpdate(BaseModel):
    payout_ids: list[int] = Field(..., min_length=1, max_length=500)
    status: PayoutStatus
    note: Optional[str] = Field(None, max_length=500)
