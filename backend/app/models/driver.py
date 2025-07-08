from sqlalchemy import Sequence, Column, Integer, String, TIMESTAMP, ForeignKey, func, UniqueConstraint, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from models.base import Base

"""Driver table holds the data for each tenant's driver"""

class Drivers(Base):
    __tablename__ = "drivers"

    id = Column(UUID(as_uuid =True), primary_key=True, default=uuid.uuid4, unique=True)
    tenant_id = Column(UUID(as_uuid =True), ForeignKey("tenants.id", ondelete="CASCADE"))

    email = Column(String(200), unique = True, nullable = False,index=True)
    phone_no = Column(String(200),nullable=True,index=True)
    first_name =  Column(String(200), nullable=False)
    last_name =  Column(String(200), nullable=False)
    password = Column(String, nullable=False)
    state = Column(String, nullable=True, index=True)
    postal_code = Column(String, nullable=True)

    completed_rides = Column(String,nullable=False)

    
    license_number = Column(String(100), nullable=True, unique=True)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True)

    
    is_active =  Column(Boolean, default=True)
    status = Column(String(50), default = "available")
    
    created_on = Column(TIMESTAMP(timezone = True), nullable=False
                        ,server_default=text('now()'))
    updated_on = Column(TIMESTAMP(timezone=True), onupdate= func.now())

    
    __table_args__ = (
        UniqueConstraint('email', 'tenant_id', name = 'unique_driver'),
    )
    
    #relationships 
    tenant = relationship("Tenants", backref="drivers", passive_deletes=True)
    vehicle = relationship("Vehicles", backref="assigned_driver", passive_deletes=True)



@property
def full_name(self):
    """Return the full name of the users"""
    return f"{self.first_name} {self.last_name}"

