from app.models.base import Base
from sqlalchemy import Sequence, Column, Integer, String, TIMESTAMP, ForeignKey, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text


id_seq =  Sequence('id_seq', start= 1050)

class Vehicles(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, Sequence('id_seq'), primary_key=True)

    # id = Column(UUID(as_uuid =True), primary_key=True, default=uuid.uuid4, unique=True)

    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    
    name = Column(String(200), nullable=False)     # e.g. "Executive SUV"
    model = Column(String(200), nullable=False)    # e.g. "Escalade"
    year = Column(Integer, nullable=True)

    license_plate = Column(String(50), unique=True, nullable=True)
    color = Column(String(50), nullable=True)
    seating_capacity = Column(Integer, nullable=True)
    status = Column(String(50), default="available")  # e.g. "available", "in_use", "maintenance"

    created_on = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_on = Column(TIMESTAMP(timezone=True), onupdate=func.now())

    tenant = relationship("Tenants", backref="vehicles", passive_deletes=True)