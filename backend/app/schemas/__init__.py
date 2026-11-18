from schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from schemas.profile import HouseholdProfileCreate, HouseholdProfileResponse
from schemas.electricity import ElectricityConsumptionCreate, ElectricityConsumptionResponse
from schemas.water import WaterConsumptionCreate, WaterConsumptionResponse
from schemas.summary import (
    ElectricitySummaryMetrics,
    WaterSummaryMetrics,
    ConsumptionSummaryResponse,
)
from schemas.ml import (
    DailyReadingInput,
    ElectricityPredictionRequest,
    ElectricityPredictionResponse,
    WaterPredictionRequest,
    WaterPredictionResponse,
    MLModelStatusResponse,
)

__all__ = [
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
    "HouseholdProfileCreate",
    "HouseholdProfileResponse",
    "ElectricityConsumptionCreate",
    "ElectricityConsumptionResponse",
    "WaterConsumptionCreate",
    "WaterConsumptionResponse",
    "ElectricitySummaryMetrics",
    "WaterSummaryMetrics",
    "ConsumptionSummaryResponse",
    "DailyReadingInput",
    "ElectricityPredictionRequest",
    "ElectricityPredictionResponse",
    "WaterPredictionRequest",
    "WaterPredictionResponse",
    "MLModelStatusResponse",
]

