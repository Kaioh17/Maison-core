from sqlalchemy import Table, Column, Integer, ForeignKey
from app.models.base import Base
from sqlalchemy.orm import relationship

vehicle_vehicle_config_association = Table(
    "vehicle_vehicle_config_association",
    Base.metadata,
    Column("vehicle_id", Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), primary_key=True),
    Column("vehicle_config_id", Integer, ForeignKey("vehicle_config.id", ondelete="CASCADE"), primary_key=True)
)