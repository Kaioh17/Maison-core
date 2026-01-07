from app.models.base import Base
from sqlalchemy import CheckConstraint, Sequence, Column, Integer, Float, String, TIMESTAMP, ForeignKey,Boolean, UniqueConstraint, and_, func, or_
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
import uuid
from sqlalchemy.dialects.postgresql import JSONB



"""Tenants table hold every client"""
id_seq =  Sequence('id_seq', start= 150)

class TenantSettings(Base):
    __tablename__ = "tenants_settings"
    # id = Column(Integer, id_seq, primary_key=True, server_default=id_seq.next_value())
    # id = Column(UUID(as_uuid =True), primary_key=True, default=uuid.uuid4, unique=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete = "CASCADE"),primary_key=True, nullable=False, unique = True)
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
    "show_vehicle_images": false,
    "types": {"airport":{"is_deposit_required":false}
                         
              "dropoffs":{"is_deposit_required":false}
                          
              "hourly": {"is_deposit_required":false}
              }
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
    
    # id = Column(Integer, id_seq, primary_key=True, server_default=id_seq.next_value())
    # id = Column(UUID(as_uuid =True), primary_key=True, default=uuid.uuid4, unique=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id",ondelete = "CASCADE"), primary_key=True,nullable=False, unique = True)
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

class TenantBookingPricing(Base):
    __tablename__ = "tenant_booking_price"
    id = Column(Integer, id_seq, primary_key=True, server_default=id_seq.next_value())
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete = "CASCADE"),nullable=False)
    
    service_type = Column(String,nullable=False, index=True) #Airport, dropoff, or hourly
    
    stc_rate = Column(Float,nullable=True, index=True, default=None) #For airports only  [STC(Surface Transport Charge)]
    gratuity_rate = Column(Float,nullable=True, index=True, default=None) #For airports only  [Percentage]
    airport_gate_fee = Column(Float,nullable=True, index=True, default=None) #For airports only  [flat fee]
    meet_and_greet_fee = Column(Float,nullable=True, index=True, default=None) #For airports only  [flat fee]
    
    deposit_type = Column(String,CheckConstraint("deposit_type IN ('percentage', 'flat')", name="check_deposit_type"), nullable = False, default=None, index=True) #percentage, flat fee
    deposit_fee = Column(Float, nullable=True, default=0.0) #0.5 --> 50% and $50.0
    created_on = Column(TIMESTAMP(timezone = True), nullable=False
                        ,server_default=text('now()'))
    updated_on = Column(TIMESTAMP(timezone=True), onupdate= func.now(), nullable=True)
    
    #relationships
    tenant = relationship("Tenants", back_populates='booking_pricing', uselist=True)
    
    __table_args__ = (
      UniqueConstraint('service_type', 'tenant_id', name = 'uq_tenant_booking'),
      # UniqueConstraint('vehicle_id', 'pickup_time', 'dropoff_time', name = 'uq_vehicle_booking')
      CheckConstraint(
        or_(
          service_type == 'airport',
          and_(                       # If it IS not airport, ALL these must be NULL
                    stc_rate.is_(None),
                    gratuity_rate.is_(None),
                    airport_gate_fee.is_(None),
                    meet_and_greet_fee.is_(None)
                )
        ),
        name="enforce_airport_fees_if_airport_service"
        ),
    )
  
class TenantPricing(Base):
    __tablename__ = "tenant_pricing"
    
    # id = Column(Integer, id_seq, primary_key=True, server_default=id_seq.next_value())
    # id = Column(UUID(as_uuid =True), primary_key=True, default=uuid.uuid4, unique=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete = "CASCADE"),primary_key=True, nullable=False, unique = True)
    base_fare = Column(Float, nullable=False, default=0.0, server_default=text('0.0'))
    per_mile_rate = Column(Float, nullable=False, default=0.0, server_default=text('0.0'))
    per_minute_rate = Column(Float, nullable=True, default=0.0, server_default=text('0.0'))
    per_hour_rate = Column(Float, nullable=False, default=0.0, server_default=text('0.0'))
    
    # deposit_config = Column(JSONB, nullable=True, default=0.0)
    # """
    # {
    #   "booking_deposits":{
    #   "airport":{"deposit_fee":0.0},
    #   "dropoffs":{"deposit_fee":0.0},
    #   "hourly": {"deposit_fee":0.0}
    # }}  
    # """
    cancellation_fee =  Column(Float, nullable=False, default= 0.0, server_default= '0.0')
    discounts = Column(Boolean, nullable=False, default=False, server_default=text('false'))
    created_on = Column(TIMESTAMP(timezone = True), nullable=False
                        ,server_default=text('now()'))
    updated_on = Column(TIMESTAMP(timezone=True), onupdate= func.now(), nullable=True)
    
    #relationships
    tenant = relationship("Tenants", back_populates='pricing', uselist=False)
    
    