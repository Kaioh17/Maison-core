from app.models.base import Base
from sqlalchemy import CheckConstraint, Sequence, Column, Integer,Float ,String, TIMESTAMP, ForeignKey,Boolean, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
import uuid

id_seq =  Sequence('id_seq', start= 150)


class BookingRatings(Base):
    __tablename__ ="booking_ratings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    rider_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    rating_value = Column(Float, nullable=False)  # 1.0 - 5.0 in 0.5 steps
    review_comment = Column(String, nullable=True)
    created_on = Column(TIMESTAMP(timezone = True), nullable=False
                        ,server_default=text('now()'))
    updated_on = Column(TIMESTAMP(timezone=True), onupdate= func.now(), nullable=True)

    __table_args__ = (
        CheckConstraint("rating_value >= 1.0 AND rating_value <= 5.0", name="rating_value_range_check"),
        CheckConstraint("(rating_value * 2) = floor(rating_value * 2)", name="rating_value_step_check"),
        UniqueConstraint("booking_id", "rider_id", name="uq_booking_rider_rating"),
    )