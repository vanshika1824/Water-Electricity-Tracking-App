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
from schemas.summary import (
    ConsumptionSummaryResponse,
    ElectricitySummaryMetrics,
    WaterSummaryMetrics,
)
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


# ==========================================
# CONSUMPTION SUMMARY / ANALYTICS
# ==========================================

@router.get("/summary", response_model=ConsumptionSummaryResponse)
def get_consumption_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve comprehensive consumption summary for the authenticated resident.

    Includes:
    - Household profile details and member counts.
    - Latest electricity and water records.
    - Per-person normalized consumption metrics.
    - Month-over-month change vs immediately preceding entry (percentage and absolute delta)
      only when two comparable records exist. Returns null when comparison is unavailable.
    - Recent logged history (up to 6 entries).

    Note on Trend Calculations & Assumptions:
    - Records currently track creation timestamp metadata (`created_at`) rather than explicit,
      verified billing cycle dates. Trends compare the most recent chronological entry against
      its immediately preceding logged entry.
    - Estimated daily per-person water consumption assumes a standardized 30-day month.
    - If fewer than two records exist, or if the baseline comparison record was 0,
      the percentage change returns null rather than an invented or infinite value.
    """
    profile = db.query(HouseholdProfile).filter(HouseholdProfile.user_id == current_user.id).first()
    if not profile:
        return ConsumptionSummaryResponse(
            has_profile=False,
            profile=None,
            electricity=ElectricitySummaryMetrics(),
            water=WaterSummaryMetrics(),
            recent_electricity_records=[],
            recent_water_records=[]
        )

    # Fetch electricity records ordered newest first (by created_at desc, id desc)
    elec_records = (
        db.query(ElectricityConsumption)
        .filter(ElectricityConsumption.profile_id == profile.id)
        .order_by(ElectricityConsumption.created_at.desc(), ElectricityConsumption.id.desc())
        .all()
    )

    # Fetch water records ordered newest first (by created_at desc, id desc)
    water_records = (
        db.query(WaterConsumption)
        .filter(WaterConsumption.profile_id == profile.id)
        .order_by(WaterConsumption.created_at.desc(), WaterConsumption.id.desc())
        .all()
    )

    members = profile.household_members if profile.household_members and profile.household_members > 0 else 1

    # -----------------------------
    # Electricity Metrics Calculation
    # -----------------------------
    latest_elec = elec_records[0] if elec_records else None
    per_person_kwh = (
        round(latest_elec.monthly_consumption_kwh / members, 2)
        if latest_elec is not None
        else None
    )

    elec_change_pct = None
    elec_change_kwh = None
    if len(elec_records) >= 2:
        curr_kwh = elec_records[0].monthly_consumption_kwh
        prev_kwh = elec_records[1].monthly_consumption_kwh
        elec_change_kwh = round(curr_kwh - prev_kwh, 2)
        if prev_kwh > 0:
            elec_change_pct = round(((curr_kwh - prev_kwh) / prev_kwh) * 100.0, 2)
        elif curr_kwh == 0:
            elec_change_pct = 0.0

    elec_summary = ElectricitySummaryMetrics(
        latest_record=latest_elec,
        per_person_kwh=per_person_kwh,
        change_pct_vs_previous=elec_change_pct,
        change_kwh_vs_previous=elec_change_kwh,
        total_records_count=len(elec_records)
    )

    # -----------------------------
    # Water Metrics Calculation
    # -----------------------------
    latest_water = water_records[0] if water_records else None
    per_person_water_monthly = (
        round(latest_water.monthly_consumption_litres / members, 2)
        if latest_water is not None
        else None
    )
    # Estimated daily litres per person assuming a standard 30-day billing month
    per_person_water_daily = (
        round(latest_water.monthly_consumption_litres / (members * 30.0), 2)
        if latest_water is not None
        else None
    )

    water_change_pct = None
    water_change_litres = None
    if len(water_records) >= 2:
        curr_litres = water_records[0].monthly_consumption_litres
        prev_litres = water_records[1].monthly_consumption_litres
        water_change_litres = round(curr_litres - prev_litres, 2)
        if prev_litres > 0:
            water_change_pct = round(((curr_litres - prev_litres) / prev_litres) * 100.0, 2)
        elif curr_litres == 0:
            water_change_pct = 0.0

    water_summary = WaterSummaryMetrics(
        latest_record=latest_water,
        per_person_litres_monthly=per_person_water_monthly,
        per_person_litres_daily=per_person_water_daily,
        change_pct_vs_previous=water_change_pct,
        change_litres_vs_previous=water_change_litres,
        total_records_count=len(water_records)
    )

    return ConsumptionSummaryResponse(
        has_profile=True,
        profile=profile,
        electricity=elec_summary,
        water=water_summary,
        recent_electricity_records=elec_records[:6],
        recent_water_records=water_records[:6]
    )

