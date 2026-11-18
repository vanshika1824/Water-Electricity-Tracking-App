import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class DailyReadingInput(BaseModel):
    """A single daily utility consumption measurement."""
    date: datetime.date = Field(..., description="Date of the reading in YYYY-MM-DD format")
    consumption: float = Field(..., ge=0.0, description="Daily consumption value (must be non-negative)")

    @field_validator("consumption")
    @classmethod
    def validate_consumption(cls, v: float) -> float:
        if v < 0.0:
            raise ValueError("Consumption value cannot be negative.")
        if v > 100_000.0:
            raise ValueError("Consumption value exceeds physical plausibility limit (100,000).")
        return v


class ElectricityPredictionRequest(BaseModel):
    """Request payload for daily electricity consumption prediction."""
    readings: List[DailyReadingInput] = Field(
        ...,
        min_length=30,
        max_length=365,
        description="List of consecutive daily readings (at least 30 consecutive calendar days required)"
    )
    target_date: Optional[datetime.date] = Field(
        None,
        description="Optional target prediction date (defaults to the day after the last reading)"
    )


class ElectricityPredictionResponse(BaseModel):
    """Response payload for daily electricity forecasting."""
    predicted_consumption_kwh: float = Field(..., description="Forecasted electricity consumption in kWh")
    prediction_date: datetime.date = Field(..., description="Calendar date of the forecasted day")
    unit: str = Field("kWh", description="Measurement unit")
    model_name: str = Field(..., description="Underlying ML algorithm name")
    model_artifact: str = Field(..., description="Model file artifact identifier")
    prediction_type: str = Field("experimental_benchmark", description="Nature of prediction")
    history_days_used: int = Field(..., description="Number of historical days used in feature calculation")
    features_summary: Dict[str, float] = Field(..., description="Extracted autoregressive and rolling features")
    data_source: str = Field(
        "UCI Individual Household Electric Power Consumption Benchmark (France)",
        description="Origin dataset of the trained benchmark weights"
    )
    disclaimer: str = Field(
        "Experimental benchmark forecast for algorithm demonstration. Represents a single European household; not calibrated to urban Indian cooling/grid dynamics.",
        description="Domain context and limitations notice"
    )


class WaterPredictionRequest(BaseModel):
    """Request payload for daily water consumption prediction."""
    readings: List[DailyReadingInput] = Field(
        ...,
        min_length=30,
        max_length=365,
        description="List of consecutive daily readings (at least 30 consecutive calendar days required)"
    )
    target_date: Optional[datetime.date] = Field(
        None,
        description="Optional target prediction date (defaults to the day after the last reading)"
    )
    benchmark_apartment_id: str = Field(
        ...,
        description="Supported benchmark apartment ID from HSB Living Lab study (APT_001 through APT_028)"
    )
    benchmark_cluster_name: Optional[str] = Field(
        None,
        description="Optional cluster identifier (e.g. CL_A through CL_I); auto-resolved if omitted"
    )


class WaterPredictionResponse(BaseModel):
    """Response payload for daily water forecasting."""
    predicted_consumption_litres: float = Field(..., description="Forecasted water consumption in Litres")
    prediction_date: datetime.date = Field(..., description="Calendar date of the forecasted day")
    unit: str = Field("Litres", description="Measurement unit")
    model_name: str = Field(..., description="Underlying ML algorithm name")
    model_artifact: str = Field(..., description="Model file artifact identifier")
    prediction_type: str = Field("experimental_benchmark", description="Nature of prediction")
    benchmark_apartment_id: str = Field(..., description="Benchmark apartment ID evaluated")
    benchmark_cluster_name: str = Field(..., description="Benchmark cluster name evaluated")
    history_days_used: int = Field(..., description="Number of historical days used in feature calculation")
    features_summary: Dict[str, float] = Field(..., description="Extracted autoregressive and rolling features")
    data_source: str = Field(
        "HSB Living Lab Fixture-Level Benchmark (Chalmers University, Sweden)",
        description="Origin dataset of the trained benchmark weights"
    )
    disclaimer: str = Field(
        "Experimental benchmark forecast for algorithm demonstration. Trained on Swedish living lab residential units with 24/7 municipal supply; not calibrated to Indian intermittent water sumps/tanks.",
        description="Domain context and limitations notice"
    )


class MLModelStatusResponse(BaseModel):
    """Status report on loaded machine learning model pipelines."""
    status: str = Field("active", description="Service status")
    model_environment: str = Field("deployment", description="Active model configuration environment ('deployment' or 'evaluation')")
    electricity_model_loaded: bool = Field(..., description="Whether electricity model pipeline is loaded")
    water_model_loaded: bool = Field(..., description="Whether water model pipeline is loaded")
    electricity_model_artifact: str = Field(..., description="Filename of electricity model")
    water_model_artifact: str = Field(..., description="Filename of water model")
    supported_water_apartments: List[str] = Field(..., description="List of recognized benchmark apartment IDs")
    minimum_history_days: int = Field(30, description="Minimum consecutive daily history required")
