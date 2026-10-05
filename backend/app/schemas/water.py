from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class WaterConsumptionCreate(BaseModel):
    monthly_consumption_litres: float = Field(..., ge=0, description="Monthly water consumption in litres")

    # Usage / context fields
    num_showers: int = Field(0, ge=0, description="Estimated total showers per day in household")
    avg_shower_duration_mins: float = Field(0.0, ge=0, description="Average shower duration in minutes")
    bucket_usage: int = Field(0, ge=0, description="Average bucket baths / usage per day")
    washing_machine_usage: Optional[str] = Field(None, max_length=100, description="e.g. 4 cycles/week")
    garden_watering: Optional[str] = Field(None, max_length=100, description="e.g. Daily, 3 times/week, None")
    vehicle_washing: Optional[str] = Field(None, max_length=100, description="e.g. Weekly, Once a month, None")
    water_pump_usage: Optional[str] = Field(None, max_length=100, description="e.g. 30 mins/day, 1 hour/day")
    other_water_usage: Optional[str] = Field(None, max_length=255, description="Other notes (e.g. cooler, swimming pool)")


class WaterConsumptionResponse(BaseModel):
    id: int
    profile_id: int
    monthly_consumption_litres: float

    num_showers: int
    avg_shower_duration_mins: float
    bucket_usage: int
    washing_machine_usage: Optional[str] = None
    garden_watering: Optional[str] = None
    vehicle_washing: Optional[str] = None
    water_pump_usage: Optional[str] = None
    other_water_usage: Optional[str] = None

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
