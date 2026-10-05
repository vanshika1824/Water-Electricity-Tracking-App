from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.profile import HouseholdProfile
from models.user import User
from schemas.profile import HouseholdProfileCreate, HouseholdProfileResponse
from services.auth_service import get_current_user

router = APIRouter(prefix="/profile", tags=["Household Profile"])


@router.get("", response_model=HouseholdProfileResponse)
def get_household_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve the household profile of the logged-in user."""
    profile = db.query(HouseholdProfile).filter(HouseholdProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Household profile has not been created yet."
        )
    return profile


@router.post("", response_model=HouseholdProfileResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_household_profile(
    profile_in: HouseholdProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create or update the household profile for the logged-in user."""
    existing_profile = db.query(HouseholdProfile).filter(HouseholdProfile.user_id == current_user.id).first()

    if existing_profile:
        # Update existing profile
        existing_profile.household_members = profile_in.household_members
        existing_profile.house_type = profile_in.house_type
        existing_profile.location = profile_in.location
        existing_profile.num_bathrooms = profile_in.num_bathrooms
        existing_profile.people_usually_at_home = profile_in.people_usually_at_home
        existing_profile.unusual_occupancy = profile_in.unusual_occupancy or "None"

        db.commit()
        db.refresh(existing_profile)
        return existing_profile

    # Create new profile
    new_profile = HouseholdProfile(
        user_id=current_user.id,
        household_members=profile_in.household_members,
        house_type=profile_in.house_type,
        location=profile_in.location,
        num_bathrooms=profile_in.num_bathrooms,
        people_usually_at_home=profile_in.people_usually_at_home,
        unusual_occupancy=profile_in.unusual_occupancy or "None"
    )
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    return new_profile
