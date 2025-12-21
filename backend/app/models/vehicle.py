from app.models.base import Base
from sqlalchemy import CheckConstraint, Sequence, Column, Integer, String, TIMESTAMP, ForeignKey, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from .juctions import vehicle_vehicle_config_association
from sqlalchemy.dialects.postgresql import JSONB


id_seq =  Sequence('id_seq', start= 1050)

class Vehicles(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, Sequence('id_seq'), primary_key=True)

    # id = Column(UUID(as_uuid =True), primary_key=True, default=uuid.uuid4, unique=True)

    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="CASCADE"), index=True, nullable=True)
    driver = relationship("Drivers", foreign_keys=[driver_id], passive_deletes=True)
    ##vehicle info
    
    make = Column(String(200), nullable=False, index=True)     # e.g. "Mercedes"
    model = Column(String(200), nullable=False, index=True)    # e.g. "GLS"
    year = Column(Integer, nullable=True, index=True)
    seating_capacity =  Column(Integer, nullable = True, index=True)
    vehicle_images = Column(JSONB,nullable=True, index=True) 
    vehicle_category_id = Column(Integer, ForeignKey("vehicle_category_rate.id"), nullable = True)

    license_plate = Column(String(50), unique=True, nullable=True)
    color = Column(String(50), nullable=True, index=True)
    status = Column(String(50),
                    CheckConstraint( "status IN ('available', 'in_use', 'maintenance')", 
                                    name="check_driver_status"
                                    ), default="available" , index=True)  # e.g. "available", "in_use", "maintenance"

    created_on = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_on = Column(TIMESTAMP(timezone=True), onupdate=func.now())

    vehicle_category = relationship("VehicleCategoryRate",
                                    foreign_keys= [vehicle_category_id], 
                                    back_populates = "vehicles")
    
    @property
    def vehicle_name(self):
        return f"{self.make}-{self.model}-{self.year}"


