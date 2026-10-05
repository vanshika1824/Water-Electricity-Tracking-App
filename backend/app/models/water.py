from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from database import Base


class WaterConsumption(Base):
    __tablename__ = "water_consumption"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("household_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    monthly_consumption_litres = Column(Float, nullable=False)

    # Usage / context fields
    num_showers = Column(Integer, default=0, nullable=False)
    avg_shower_duration_mins = Column(Float, default=0.0, nullable=False)
    bucket_usage = Column(Integer, default=0, nullable=False)
    washing_machine_usage = Column(String(100), nullable=True)
    garden_watering = Column(String(100), nullable=True)
    vehicle_washing = Column(String(100), nullable=True)
    water_pump_usage = Column(String(100), nullable=True)
    other_water_usage = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship
    profile = relationship("HouseholdProfile", back_populates="water_records")
