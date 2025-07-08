from models.base import Base
from sqlalchemy import Sequence, Column, Integer, String, TIMESTAMP, ForeignKey, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

"""Users table holds the info of each tenant's customers"""

class Users(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid =True), primary_key=True, default=uuid.uuid4, unique=True)
    email = Column(String(200), unique = True, nullable = False,index=True)
    phone_no = Column(String(200),nullable=True,index=True)
    first_name =  Column(String(200), nullable=False)
    last_name =  Column(String(200), nullable=False)
    password = Column(String, nullable=False)
    address = Column(String,nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True, index=True)
    country = Column(String, nullable=True, index = True)
    postal_code = Column(String, nullable=True)

    
    role = Column(String, nullable=False, index=True, default='rider')
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"))
    created_on = Column(TIMESTAMP(timezone = True), nullable=False
                        ,server_default=text('now()'))
    updated_on = Column(TIMESTAMP(timezone=True), onupdate= func.now())

    tier = Column(String, )
    
    __table_args__ = (
        UniqueConstraint('email', 'tenant_id', name = 'unique_user'),
    )
    
    #relationships 
    tenants = relationship("Tenants", back_populates="users")



@property
def full_name(self):
    """Return the full name of the users"""
    return f"{self.first_name} {self.last_name}"

