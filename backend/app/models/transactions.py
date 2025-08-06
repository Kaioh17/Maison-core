from app.models.base import Base
from sqlalchemy import CheckConstraint, Sequence, Column, Integer,Float ,String, TIMESTAMP, ForeignKey,Boolean, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
import uuid

id_seq =  Sequence('id_seq', start= 150)


class Transaction(Base):
    __tablename__ ="transactions"

    id = Column(Integer,Sequence('id_seq'),primary_key=True )
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    stripe_payment_intent_id = Column(String(255), nullable=True)
    amount = Column(Float, nullable=False, default=0.0, server_default="0.0")
    platform_fee_amount = Column(Float, nullable=True)
    currency =  Column(String(3), default='usd', server_default='usd', nullable=False)
    status = Column(String(50), default='pending', nullable=False,
                    server_default='pending')
    created_on = Column(TIMESTAMP(timezone = True), nullable=False
                        ,server_default=text('now()'))
    updated_on = Column(TIMESTAMP(timezone=True), onupdate= func.now(), nullable=True)

 
