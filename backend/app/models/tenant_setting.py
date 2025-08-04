from app.models.base import Base
from sqlalchemy import CheckConstraint, Sequence, Column, Integer, Float, String, TIMESTAMP, ForeignKey,Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
import uuid



"""Tenants table hold every client"""
id_seq =  Sequence('id_seq', start= 150)

class TenantSettings(Base):
    __tablename__ = "tenants_settings"
    id = Column(Integer, id_seq, primary_key=True, server_default=id_seq.next_value())
    # id = Column(UUID(as_uuid =True), primary_key=True, default=uuid.uuid4, unique=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete = "CASCADE"), nullable=False, unique = True)
    
    #branding
    theme = Column(String, nullable=False, default="dark", server_default=text("'dark'"))
    logo_url = Column(String, nullable= True)
    slug = Column(String, unique=True, nullable = False, index=True)
    enable_branding = Column(Boolean, nullable=False, default=False, server_default=text('False'))
    #fare
    base_fare = Column(Float, nullable=False, default=0.0, server_default=text('0.0'))
    per_mile_rate = Column(Float, nullable=False, default=0.0, server_default=text('0.0'))
    per_minute_rate = Column(Float, nullable=True, default=0.0, server_default=text('0.0'))
    per_hour_rate = Column(Float, nullable=False, default=0.0, server_default=text('0.0'))
    #rider
    rider_tiers_enabled = Column(Boolean, nullable=False, default=False, server_default='False')
    cancellation_fee =  Column(Float, nullable=False, default= 0.0, server_default= '0.0')
    

    discounts = Column(Boolean, nullable=False, default=False, server_default=text('false'))
    created_on = Column(TIMESTAMP(timezone = True), nullable=False
                        ,server_default=text('now()'))
    updated_on = Column(TIMESTAMP(timezone=True), onupdate= func.now(), nullable=True)