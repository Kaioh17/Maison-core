from sqlalchemy import Sequence,CheckConstraint, Column, Integer, String, TIMESTAMP, ForeignKey, func, UniqueConstraint, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from app.models.base import Base

id_seq =  Sequence('id_seq', start= 150)

"""A vehicle can have only one driver 1:1 relationship"""

class Admin(Base):
    __tablename__ = "admin"
    id = Column(Integer, Sequence('id_seq'), primary_key=True)
    first_name = Column(String(200),nullable=False,index=True )
    last_name = Column(String(200), nullable=False, index=True)
    email = Column(String(200), nullable = False,index=True)
    password = Column(String, nullable= False)
    totp = Column(String, nullable=True)
    role=Column(String, server_default='admin')
    created_on = Column(TIMESTAMP(timezone = True), nullable=False
                        ,server_default=text('now()'))
    updated_on = Column(TIMESTAMP(timezone=True), onupdate= func.now())
