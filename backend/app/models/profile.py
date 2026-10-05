from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from database import Base


class HouseholdProfile(Base):
    __tablename__ = "household_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    household_members = Column(Integer, nullable=False)
    house_type = Column(String(50), nullable=False)  # Apartment, Independent House, Other
    location = Column(String(150), nullable=False)
    num_bathrooms = Column(Integer, nullable=False)

    people_usually_at_home = Column(Integer, nullable=True)
    unusual_occupancy = Column(String(50), default="None", nullable=True)  # None, Guests, Vacation, Other

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="profile")
    electricity_records = relationship(
        "ElectricityConsumption",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="desc(ElectricityConsumption.created_at)"
    )
    water_records = relationship(
        "WaterConsumption",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="desc(WaterConsumption.created_at)"
    )
