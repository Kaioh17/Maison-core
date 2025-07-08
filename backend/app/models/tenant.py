from models.base import Base
from sqlalchemy import CheckConstraint, Sequence, Column, Integer, String, TIMESTAMP, ForeignKey,Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
import uuid

"""Tenants table hold every client"""
tenant_id_seq =  Sequence('user_id_seq', start= 150)

class Tenants(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid =True), primary_key=True, default=uuid.uuid4, unique=True)
    email = Column(String(200), unique = True, nullable = False,index=True)    
    first_name =  Column(String(200), nullable=False)
    last_name =  Column(String(200), nullable=False)
    password = Column(String, nullable=False)
    phone_no = Column(String(200), nullable=False, index = True)

    company_name = Column(String(200),unique=True, nullable=False, index = True)
    logo_url = Column(String, nullable= True)
    slug = Column(String, unique=True, nullable = False, index=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False, index=True)

    created_on = Column(TIMESTAMP(timezone = True), nullable=False
                        ,server_default=text('now()'))
    updated_on = Column(TIMESTAMP(timezone=True), onupdate= func.now())
    
    drivers = Column(Integer, nullable=False, index=True)
    is_verified = Column(Boolean, default=False)
    plan = Column(String, nullable=False, default= "free")
    is_active = Column(Boolean, default=True)
    
    # relation ships
    users = relationship("Users", back_populates="tenant", cascade= "all, delete", passive_deletes=True)

    #constraints
    __table_args__ = (
        CheckConstraint('drivers > 0', name = 'check_drivers_positive'),
        CheckConstraint("plan IN ('free', 'basic', 'premium', 'enterprise')", name='check_plan_valid'),
    )
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, company_name='{self.company_name}')>"

    @property
    def full_name(self):
        """Return the full name of the tenant"""
        return f"{self.first_name} {self.last_name}"