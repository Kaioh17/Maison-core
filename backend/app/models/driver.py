from sqlalchemy import Sequence, Column, Integer, String, TIMESTAMP, ForeignKey, func, UniqueConstraint, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from app.models.base import Base

id_seq =  Sequence('id_seq', start= 150)

 

class Drivers(Base):
    __tablename__ = "drivers"
    id = Column(Integer, Sequence('id_seq'), primary_key=True)
    # id = Column(UUID(as_uuid =True), primary_key=True, default=uuid.uuid4, unique=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"))

    email = Column(String(200), nullable = False,index=True)
    phone_no = Column(String(200),nullable=True,index=True)
    first_name =  Column(String(200), nullable=False)
    last_name =  Column(String(200), nullable=False)
    

    password = Column(String, nullable= True)
    state = Column(String, nullable=True, index=True)
    postal_code = Column(String, nullable=True)
    role = Column(String, nullable = True, default="driver")

    ##driver_type 
    driver_type = Column(String, nullable=False)
    

    completed_rides = Column(String, nullable=False, default=0, server_default=text("0"))

    
    license_number = Column(String(100), nullable=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True)

    driver_token = Column(String,nullable=False)
    is_registered = Column(String, nullable=False, default="not_registered")
    is_active =  Column(Boolean, default=False)
    status = Column(String(50), default = "available")
    
    created_on = Column(TIMESTAMP(timezone = True), nullable=False
                        ,server_default=text('now()'))
    updated_on = Column(TIMESTAMP(timezone=True), onupdate= func.now())

    #stripe configuration
    stripe_account_id = Column(String(255), nullable=True, index=True)
    background_check_status = Column(String(50),nullable=True, default='pending')
    stripe_onboaring_complete = Column(Boolean, nullable=True, default=False)

    
    __table_args__ = (
        UniqueConstraint('email', 'tenant_id','license_number', name = 'unique_driver'),
    )
    
    #relationships 
    tenant = relationship("Tenants",passive_deletes=True)
    vehicle = relationship("Vehicles", foreign_keys=[vehicle_id], passive_deletes=True)



    @property
    def full_name(self):
        """Return the full name of the users"""
        return f"{self.first_name} {self.last_name}"

