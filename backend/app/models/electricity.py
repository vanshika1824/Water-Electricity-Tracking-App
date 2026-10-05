from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from database import Base


class ElectricityConsumption(Base):
    __tablename__ = "electricity_consumption"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("household_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    monthly_consumption_kwh = Column(Float, nullable=False)

    # Appliance quantities
    ac_count = Column(Integer, default=0, nullable=False)
    fan_count = Column(Integer, default=0, nullable=False)
    refrigerator_count = Column(Integer, default=0, nullable=False)
    tv_count = Column(Integer, default=0, nullable=False)
    geyser_count = Column(Integer, default=0, nullable=False)
    washing_machine_count = Column(Integer, default=0, nullable=False)
    water_pump_count = Column(Integer, default=0, nullable=False)
    other_appliances = Column(String(255), nullable=True)

    # Context / approximate usage duration or frequency
    usage_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship
    profile = relationship("HouseholdProfile", back_populates="electricity_records")
