from app.models.base import Base
from sqlalchemy import CheckConstraint, Sequence, Column, Integer, String, TIMESTAMP, ForeignKey,Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
import uuid

"""Tenants table hold every client"""
id_seq =  Sequence('id_seq', start= 150)
    
# TODO switch all ids to uuid
class Tenants(Base):
    __tablename__ = "tenants"
    id = Column(Integer, id_seq, primary_key=True, server_default=id_seq.next_value())
    # id = Column(UUID(as_uuid =True), primary_key=True, default=uuid.uuid4, unique=True)
    email = Column(String(200), unique = True, nullable = False,index=True)    
    first_name =  Column(String(200), nullable=False)
    last_name =  Column(String(200), nullable=False)
    password = Column(String, nullable=False)
    phone_no = Column(String(200), nullable=False, index = True)
    role = Column(String, nullable=False, index=True, default = "tenant")
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_on = Column(TIMESTAMP(timezone = True), nullable=False
                        ,server_default=text('now()'))
    updated_on = Column(TIMESTAMP(timezone=True), onupdate= func.now(), nullable=True)
    
    profile = relationship(
        "TenantProfile",
        # primaryjoin="Tenant.id == foreign(TenantProfile.tenant_id)",
        # back_populates="tenants_profile",
        uselist=False,
        cascade="all, delete-orphan"
    )

    stats = relationship(
        "TenantStats",
        # primaryjoin="Tenant.id == foreign(TenantStats.tenant_id)",        
        # back_populates="tenants_stats",
        uselist=False,
        cascade="all, delete-orphan"
    )
    users = relationship("Users", back_populates="tenants", cascade= "all, delete", passive_deletes=True)


    @property
    def full_name(self):
        """Return the full name of the tenant"""
        return f"{self.first_name} {self.last_name}"
    
   
    
class TenantProfile(Base): 
    __tablename__ = "tenants_profile"
    """Tenanat business profile"""
    tenant_id = Column(Integer,ForeignKey("tenants.id", ondelete="CASCADE") ,primary_key = True)
    company_name = Column(String(200),unique=True, nullable=False, index = True)
    logo_url = Column(String, nullable= True)
    slug = Column(String, unique=True, nullable = False, index=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=False, index=True)   
    
    stripe_customer_id = Column(String, nullable=True, index=True)
    stripe_account_id =  Column(String, nullable=True, index=True)
    subscription_status = Column(String, nullable=True, default= "free")
    subscription_plan = Column(String, nullable=True, default="free")
    created_on = Column(TIMESTAMP(timezone = True), nullable=False
                        ,server_default=text('now()'))
    updated_on = Column(TIMESTAMP(timezone=True), onupdate= func.now(), nullable=True)
    
    tenant = relationship("Tenants", back_populates="profile", uselist=False)
    
    @property
    def company(self):
        """Return company name"""
        return f"{self.company_name}"
    # alter table tenants_profile add constraint FK_tenant_id foreign key (tenant_id) references tenants_info (id) on delete cascade;
class TenantStats(Base):
    __tablename__ = "tenants_stats"
    tenant_id = Column(Integer,  ForeignKey("tenants.id", ondelete="CASCADE"), primary_key = True, unique=True, nullable=False, index=True)
    drivers_count = Column(Integer, nullable=False, index=True)
    daily_ride_count = Column(Integer, nullable=True, default=0, server_default= "0")
    last_ride_count_reset = Column(TIMESTAMP(timezone=True), nullable=True)
    total_ride_count = Column(Integer, nullable=False, default=0, server_default="0")
    created_on = Column(TIMESTAMP(timezone = True), nullable=False
                        ,server_default=text('now()'))
    updated_on = Column(TIMESTAMP(timezone=True), onupdate= func.now(), nullable=True)
    
    tenant = relationship("Tenants", back_populates="stats", uselist=False)
    