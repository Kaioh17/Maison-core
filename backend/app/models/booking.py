from app.models.base import Base
from sqlalchemy import CheckConstraint, Sequence, Column, Integer,Float ,String, TIMESTAMP, ForeignKey,Boolean, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
import uuid

id_seq =  Sequence('id_seq', start= 150)


class Bookings(Base):
    __tablename__ = "bookings"
    id = Column(Integer, Sequence('id_seq'), primary_key=True)
    # id = Column(UUID(as_uuid =True), primary_key=True, default=uuid.uuid4, unique=True)
    driver_id = Column(Integer,ForeignKey("drivers.id"), nullable=True)
    tenant_id = Column(Integer,ForeignKey("tenants.id", ondelete= "CASCADE"), nullable=False)
    vehicle_id = Column(Integer,ForeignKey("vehicles.id"), nullable=True)
    service_type = Column(String, nullable=False)
    rider_id = Column(Integer, ForeignKey("users.id", ondelete= "CASCADE"), nullable=False)
    pickup_location = Column(String, nullable=False)
    pickup_time = Column(TIMESTAMP(timezone=True), nullable=False)
    dropoff_location = Column(String, nullable=True)
    dropoff_time = Column(TIMESTAMP(timezone=True), nullable=True)
    city = Column(String, nullable=True)
    booking_status = Column(String, nullable=False, default = 'pending', server_default=text("'pending'"))
    estimated_price =  Column(Float, nullable=True)
    payment_method = Column(String, nullable=True)
    notes = Column(String, nullable=False)
    created_on = Column(TIMESTAMP(timezone = True), nullable=False
                        ,server_default=text('now()'))
    updated_on = Column(TIMESTAMP(timezone=True), onupdate= func.now(), nullable=True)


    __table_args__ = (
        UniqueConstraint('driver_id', 'pickup_time', 'dropoff_time', name = 'uq_driver_booking'),
        UniqueConstraint('vehicle_id', 'pickup_time', 'dropoff_time', name = 'uq_vehicle_booking')

    )