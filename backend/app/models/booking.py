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
    vehicle_id = Column(Integer,ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=False)
    service_type = Column(String, nullable=False) # airport service, 
    airport_service = Column(String,CheckConstraint("airport_service IN ('from_airport', 'to_airport')", name='airport_service_check'),nullable=True ) #from_airport or to_airport
    rider_id = Column(Integer, ForeignKey("users.id", ondelete= "CASCADE"), nullable=False)
    pickup_location = Column(String, nullable=False)
    pickup_time = Column(TIMESTAMP(timezone=True), nullable=False)
    hours = Column(Float, nullable=True) 
    dropoff_location = Column(String, nullable=True)
    dropoff_time = Column(TIMESTAMP(timezone=True), nullable=True)
    country = Column(String, nullable=True)
    booking_status = Column(String,CheckConstraint("booking_status IN ('pending', 'completed', 'cancelled', 'delayed')",name="booking_status_check_connstraint") ,nullable=False, default = 'pending', server_default=text("'pending'"))
    estimated_price =  Column(Float, nullable=True)
    payment_method = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    is_approved=Column(Boolean, nullable=True, default=False) ## column to check if ride was approved by rider 
    #Stripe payment configuratioin
    # payment_status = Column(Boolean,CheckConstraint("booking_status IN ('declined', 'paid')",name="payment_status"), nullable=True, default=False)
    platform_fee_amount = Column(Float, nullable=True)
    payment_status = Column(String,CheckConstraint("payment_status IN ('pending', 'full_paid', 'deposit_paid', 'balance_paid')",name="booking_status_check_connstraint"), nullable=True, default="pending", server_default= "pending")
    deposit_intent_id = Column(String, nullable=True, index=True)#switc to nullable false after cleaning db
    balance_intent_id = Column(String, nullable=True, index=True)#switc to nullable false after cleaning db
    payment_id = Column(String, nullable=True, index=True)#switc to nullable false after cleaning db

    created_on = Column(TIMESTAMP(timezone = True), nullable=False
                        ,server_default=text('now()'))
    updated_on = Column(TIMESTAMP(timezone=True), onupdate= func.now(), nullable=True)

    vehicle = relationship("Vehicles", back_populates="bookings", uselist=False)
    tenant = relationship("Tenants", back_populates='bookings', uselist=False)
    rider = relationship("Users", back_populates='bookings', uselist=False)

    __table_args__ = (
        UniqueConstraint('driver_id', 'pickup_time', 'dropoff_time', name = 'uq_driver_booking'),
        UniqueConstraint('vehicle_id', 'pickup_time', 'dropoff_time', name = 'uq_vehicle_booking')

    )