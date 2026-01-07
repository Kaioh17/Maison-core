from app.models.base import Base
from sqlalchemy import CheckConstraint, Sequence, Column, Integer,Float, String, TIMESTAMP, ForeignKey,Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
import uuid
from sqlalchemy.dialects.postgresql import *

id_seq =  Sequence('id_seq', start= 150)


class VehicleCategoryRate(Base):
    __tablename__ = "vehicle_category_rate"
    id = Column(Integer, id_seq, primary_key=True, server_default=id_seq.next_value())
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    vehicle_category = Column(String, nullable=True, index=True)
    vehicle_flat_rate = Column(Float, nullable=False, default= 0.0, server_default=text ('0.0'))
    # vehicle_avg_speed = Column(Float, nullable=True, default=25.0, server_default= text('25.0') )
    
    allowed_image_types = Column(ARRAY(String),nullable=True, default=[
                                    "front_exterior",
                                    "rear_exterior",
                                    "side_exterior",
                                    "interior_front",
                                    "interior_rear",
                                    "trunk",
                                    "dashboard",
                                    "wheel",
                                    "feature"
                                ])
    created_on = Column(TIMESTAMP(timezone = True), nullable=False
                        ,server_default=text('now()'))
    updated_on = Column(TIMESTAMP(timezone=True), onupdate= func.now())
    
    vehicles = relationship("Vehicles",
        back_populates="vehicle_category")
