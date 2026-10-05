from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ElectricityConsumptionCreate(BaseModel):
    monthly_consumption_kwh: float = Field(..., ge=0, description="Monthly electricity consumption in kWh")

    # Appliance quantities
    ac_count: int = Field(0, ge=0, description="Number of AC units")
    fan_count: int = Field(0, ge=0, description="Number of ceiling/table fans")
    refrigerator_count: int = Field(0, ge=0, description="Number of refrigerators")
    tv_count: int = Field(0, ge=0, description="Number of TVs")
    geyser_count: int = Field(0, ge=0, description="Number of water geysers/heaters")
    washing_machine_count: int = Field(0, ge=0, description="Number of washing machines")
    water_pump_count: int = Field(0, ge=0, description="Number of electric water pumps")
    other_appliances: Optional[str] = Field(None, max_length=255, description="Other appliances (e.g., microwave, desktop)")

    # Appliance usage context
    usage_notes: Optional[str] = Field(None, max_length=500, description="Approximate usage duration or frequency")


class ElectricityConsumptionResponse(BaseModel):
    id: int
    profile_id: int
    monthly_consumption_kwh: float

    ac_count: int
    fan_count: int
    refrigerator_count: int
    tv_count: int
    geyser_count: int
    washing_machine_count: int
    water_pump_count: int
    other_appliances: Optional[str] = None
    usage_notes: Optional[str] = None

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
