from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.electricity import ElectricityConsumption
from models.profile import HouseholdProfile
from models.user import User
from models.water import WaterConsumption
from schemas.electricity import (
    ElectricityConsumptionCreate,
    ElectricityConsumptionResponse,
)
from schemas.water import WaterConsumptionCreate, WaterConsumptionResponse
from services.auth_service import get_current_user

router = APIRouter(prefix="/consumption", tags=["Consumption Tracking"])


def _get_user_profile(user_id: int, db: Session) -> HouseholdProfile:
    """Helper to ensure user has a household profile before recording consumption."""
    profile = db.query(HouseholdProfile).filter(HouseholdProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Household profile not found. Please complete your household profile first."
        )
    return profile


# ==========================================
# ELECTRICITY ENDPOINTS
# ==========================================

@router.post("/electricity", response_model=ElectricityConsumptionResponse, status_code=status.HTTP_201_CREATED)
def record_electricity_consumption(
    elec_in: ElectricityConsumptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit monthly electricity consumption data for the authenticated user's household."""
    profile = _get_user_profile(current_user.id, db)

    record = ElectricityConsumption(
        profile_id=profile.id,
        monthly_consumption_kwh=elec_in.monthly_consumption_kwh,
        ac_count=elec_in.ac_count,
        fan_count=elec_in.fan_count,
        refrigerator_count=elec_in.refrigerator_count,
        tv_count=elec_in.tv_count,
        geyser_count=elec_in.geyser_count,
        washing_machine_count=elec_in.washing_machine_count,
        water_pump_count=elec_in.water_pump_count,
        other_appliances=elec_in.other_appliances,
        usage_notes=elec_in.usage_notes
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/electricity", response_model=List[ElectricityConsumptionResponse])
def get_electricity_consumption_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all recorded electricity consumption entries for the current user."""
    profile = _get_user_profile(current_user.id, db)
    records = (
        db.query(ElectricityConsumption)
        .filter(ElectricityConsumption.profile_id == profile.id)
        .order_by(ElectricityConsumption.created_at.desc())
        .all()
    )
    return records


# ==========================================
# WATER ENDPOINTS
# ==========================================

@router.post("/water", response_model=WaterConsumptionResponse, status_code=status.HTTP_201_CREATED)
def record_water_consumption(
    water_in: WaterConsumptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit monthly water consumption data for the authenticated user's household."""
    profile = _get_user_profile(current_user.id, db)

    record = WaterConsumption(
        profile_id=profile.id,
        monthly_consumption_litres=water_in.monthly_consumption_litres,
        num_showers=water_in.num_showers,
        avg_shower_duration_mins=water_in.avg_shower_duration_mins,
        bucket_usage=water_in.bucket_usage,
        washing_machine_usage=water_in.washing_machine_usage,
        garden_watering=water_in.garden_watering,
        vehicle_washing=water_in.vehicle_washing,
        water_pump_usage=water_in.water_pump_usage,
        other_water_usage=water_in.other_water_usage
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/water", response_model=List[WaterConsumptionResponse])
def get_water_consumption_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all recorded water consumption entries for the current user."""
    profile = _get_user_profile(current_user.id, db)
    records = (
        db.query(WaterConsumption)
        .filter(WaterConsumption.profile_id == profile.id)
        .order_by(WaterConsumption.created_at.desc())
        .all()
    )
    return records
