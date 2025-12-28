from app.models.base import Base
from sqlalchemy import CheckConstraint, Sequence, Column, Integer, Float, String, TIMESTAMP, ForeignKey,Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
import uuid
from sqlalchemy.dialects.postgresql import JSONB



"""Tenants table hold every client"""
id_seq =  Sequence('id_seq', start= 150)

class TenantSettings(Base):
    __tablename__ = "tenants_settings"
    id = Column(Integer, id_seq, primary_key=True, server_default=id_seq.next_value())
    # id = Column(UUID(as_uuid =True), primary_key=True, default=uuid.uuid4, unique=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete = "CASCADE"), nullable=False, unique = True)
    rider_tiers_enabled = Column(Boolean, nullable=True, default=False, server_default='False')
    config = Column(JSONB, nullable=True)
    
    created_on = Column(TIMESTAMP(timezone = True), nullable=False
                        ,server_default=text('now()'))
    updated_on = Column(TIMESTAMP(timezone=True), onupdate= func.now(), nullable=True)
    #config josnb type
    #relationships
    """{
  "booking": {
    "allow_guest_bookings": true,
    "show_vehicle_images": false
  },
  "branding": {
    "button_radius": 8,
    "font_family": "DM Sans"
  },
  "features": {
    "vip_profiles": true,
    "show_loyalty_banner": false
  }
}
"""
    tenant = relationship("Tenants", back_populates="settings", uselist=False)

class TenantBranding(Base):
    __tablename__ = "tenant_branding"
    
    id = Column(Integer, id_seq, primary_key=True, server_default=id_seq.next_value())
    # id = Column(UUID(as_uuid =True), primary_key=True, default=uuid.uuid4, unique=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete = "CASCADE"), nullable=False, unique = True)
    theme = Column(String, nullable=False, default="dark", server_default=text("'dark'"))
    primary_color = Column(String, nullable=True)
    secondary_color = Column(String, nullable=True)
    accent_color = Column(String, nullable=True)
    favicon_url = Column(String, nullable=True)
    slug = Column(String, unique=True, nullable = True, index=True)
    email_from_name = Column(String, nullable=True) #company to email
    email_from_address = Column(String, nullable=True) #company email from address
    logo_url = Column(String, nullable= True)
    enable_branding = Column(Boolean, nullable=False, default=False, server_default=text('False'))
    
    created_on = Column(TIMESTAMP(timezone = True), nullable=False
                        ,server_default=text('now()'))
    updated_on = Column(TIMESTAMP(timezone=True), onupdate= func.now(), nullable=True)
    
    #relationships
    tenant = relationship("Tenants", back_populates="branding", uselist=False)
    
class TenantPricing(Base):
    __tablename__ = "tenant_pricing"
    
    id = Column(Integer, id_seq, primary_key=True, server_default=id_seq.next_value())
    # id = Column(UUID(as_uuid =True), primary_key=True, default=uuid.uuid4, unique=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete = "CASCADE"), nullable=False, unique = True)
    base_fare = Column(Float, nullable=False, default=0.0, server_default=text('0.0'))
    per_mile_rate = Column(Float, nullable=False, default=0.0, server_default=text('0.0'))
    per_minute_rate = Column(Float, nullable=True, default=0.0, server_default=text('0.0'))
    per_hour_rate = Column(Float, nullable=False, default=0.0, server_default=text('0.0'))
    cancellation_fee =  Column(Float, nullable=False, default= 0.0, server_default= '0.0')
    discounts = Column(Boolean, nullable=False, default=False, server_default=text('false'))
    created_on = Column(TIMESTAMP(timezone = True), nullable=False
                        ,server_default=text('now()'))
    updated_on = Column(TIMESTAMP(timezone=True), onupdate= func.now(), nullable=True)
    
    #relationships
    tenant = relationship("Tenants", back_populates='pricing', uselist=False)
    
    