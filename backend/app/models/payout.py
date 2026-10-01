from app.models.base import Base
from sqlalchemy import CheckConstraint, Sequence, Column, Integer,Float ,String, TIMESTAMP, ForeignKey,Boolean, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
import uuid

id_seq =  Sequence('id_seq', start= 150)


class Payout(Base):
    __tablename__ ="payouts"

    id = Column(Integer,Sequence('id_seq'),primary_key=True )
    driving_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    stripe_transfer_id = Column(String(255), nullable=True)
    amount = Column(Float, nullable=False, default=0.0, server_default="0.0")
    currency =  Column(String(3), default='usd', server_default='usd', nullable=False)
    # Signed net money movement for the ride: + company owes driver, - driver owes company (cash held).
    # `adjustment` is added on top by the tenant (bonus / deduction); net = amount + adjustment.
    adjustment = Column(Float, nullable=False, default=0.0, server_default="0.0")
    status = Column(String(50), default='pending', nullable=False,
                    server_default='pending')
    # Who last changed status/adjustment and when: an audit record, not a verdict.
    status_by_role = Column(String(20), nullable=True)  # 'tenant' | 'driver'
    status_by_id = Column(Integer, nullable=True)
    status_on = Column(TIMESTAMP(timezone=True), nullable=True)
    note = Column(String, nullable=True)
    created_on = Column(TIMESTAMP(timezone = True), nullable=False
                        ,server_default=text('now()'))
    updated_on = Column(TIMESTAMP(timezone=True), onupdate= func.now(), nullable=True)

    __table_args__ = (
        UniqueConstraint('booking_id', name='uq_payout_booking'),
        CheckConstraint("status IN ('pending', 'paid', 'disputed', 'verified')", name='payout_status_check'),
    )
