from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from schemas.profile import HouseholdProfileResponse
from schemas.electricity import ElectricityConsumptionResponse
from schemas.water import WaterConsumptionResponse


class ElectricitySummaryMetrics(BaseModel):
    latest_record: Optional[ElectricityConsumptionResponse] = Field(
        None, description="Most recently logged electricity record"
    )
    per_person_kwh: Optional[float] = Field(
        None, description="Monthly electricity kWh per household member based on latest record"
    )
    change_pct_vs_previous: Optional[float] = Field(
        None,
        description=(
            "Percentage change in monthly kWh compared to the immediately preceding logged entry. "
            "Returns null if fewer than 2 records exist or if previous record was 0 kWh."
        )
    )
    change_kwh_vs_previous: Optional[float] = Field(
        None,
        description=(
            "Absolute change in monthly kWh compared to the immediately preceding logged entry. "
            "Returns null if fewer than 2 records exist."
        )
    )
    total_records_count: int = Field(0, description="Total number of logged electricity records")

    model_config = ConfigDict(from_attributes=True)


class WaterSummaryMetrics(BaseModel):
    latest_record: Optional[WaterConsumptionResponse] = Field(
        None, description="Most recently logged water record"
    )
    per_person_litres_monthly: Optional[float] = Field(
        None, description="Monthly water litres per household member based on latest record"
    )
    per_person_litres_daily: Optional[float] = Field(
        None,
        description=(
            "Estimated daily litres per person (LPCD), assuming a standard 30-day billing month. "
            "Returns null if no water records exist."
        )
    )
    change_pct_vs_previous: Optional[float] = Field(
        None,
        description=(
            "Percentage change in monthly litres compared to the immediately preceding logged entry. "
            "Returns null if fewer than 2 records exist or if previous record was 0 litres."
        )
    )
    change_litres_vs_previous: Optional[float] = Field(
        None,
        description=(
            "Absolute change in monthly litres compared to the immediately preceding logged entry. "
            "Returns null if fewer than 2 records exist."
        )
    )
    total_records_count: int = Field(0, description="Total number of logged water records")

    model_config = ConfigDict(from_attributes=True)


class ConsumptionSummaryResponse(BaseModel):
    has_profile: bool = Field(..., description="Whether the user has configured a household profile")
    profile: Optional[HouseholdProfileResponse] = Field(
        None, description="Household profile demographics and occupancy details"
    )
    electricity: ElectricitySummaryMetrics = Field(..., description="Electricity consumption summary metrics")
    water: WaterSummaryMetrics = Field(..., description="Water consumption summary metrics")
    recent_electricity_records: List[ElectricityConsumptionResponse] = Field(
        default_factory=list,
        description="Recent logged electricity records in reverse chronological order (up to 6)"
    )
    recent_water_records: List[WaterConsumptionResponse] = Field(
        default_factory=list,
        description="Recent logged water records in reverse chronological order (up to 6)"
    )

    model_config = ConfigDict(from_attributes=True)
