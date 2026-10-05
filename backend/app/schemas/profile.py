from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class HouseholdProfileCreate(BaseModel):
    household_members: int = Field(..., ge=1, description="Number of household members")
    house_type: str = Field(..., min_length=2, max_length=50, description="Apartment, Independent House, Other")
    location: str = Field(..., min_length=2, max_length=150, description="City / Neighborhood")
    num_bathrooms: int = Field(..., ge=1, description="Number of bathrooms")

    people_usually_at_home: Optional[int] = Field(None, ge=0, description="People usually at home during the day")
    unusual_occupancy: Optional[str] = Field("None", max_length=50, description="None, Guests, Vacation, Other")


class HouseholdProfileResponse(BaseModel):
    id: int
    user_id: int
    household_members: int
    house_type: str
    location: str
    num_bathrooms: int
    people_usually_at_home: Optional[int] = None
    unusual_occupancy: Optional[str] = "None"
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
