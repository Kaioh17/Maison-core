from app.models.base import Base
from sqlalchemy import CheckConstraint, Sequence, Column, Integer,Float, String, TIMESTAMP, ForeignKey,Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
import uuid
from .juctions import vehicle_vehicle_config_association


id_seq =  Sequence('id_seq', start= 150)

    
"""Vehicle model and rate"""
class VehicleConfig(Base):
    __tablename__ = "vehicle_config"
    id = Column(Integer, id_seq, primary_key=True, server_default=id_seq.next_value())
    # vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete='CASCADE'), index=True, nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    vehicle_category = Column(String, nullable=True, index=True)
    seating_capacity = Column(Integer, nullable=True, index=True)
    vehicle_flat_rate = Column(Float, nullable=False, default= 0.0, server_default=text ('0.0'))
    # vehicles = relationship(
    #     "Vehicles",
    #     secondary=vehicle_vehicle_config_association,
    #     back_populates="vehicle_configs"
    # )
    
    created_on = Column(TIMESTAMP(timezone = True), nullable=False
                        ,server_default=text('now()'))
    updated_on = Column(TIMESTAMP(timezone=True), onupdate= func.now())

    # vehicles = relationship("Vehicles", foreign_keys=[vehicle_id],  passive_deletes=True)
    # vehicles = relationship("Vehicles", back_populates="vehicle_config", 
    #                          foreign_keys=[vehicle_id])
    
    