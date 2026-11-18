import os
import sys
import time
import pytest
from fastapi.testclient import TestClient

# Add app directory to sys.path so backend imports work cleanly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))

from main import app
from database import SessionLocal
from models.user import User

client = TestClient(app)


def test_health_check():
    """Verify health check endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root_endpoint():
    """Verify root endpoint returns welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "Water & Electricity Tracking App"
    assert data["status"] == "online"


def test_registration_validation_password_mismatch():
    """Verify registration fails if passwords do not match."""
    payload = {
        "full_name": "Test User",
        "email": "mismatch@example.com",
        "password": "Password123!",
        "confirm_password": "DifferentPassword!"
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 422  # Pydantic validation error


def test_user_registration_and_login_flow():
    """Verify complete registration, login, and token generation flow."""
    unique_suffix = int(time.time() * 1000)
    test_email = f"user_{unique_suffix}@example.com"
    test_password = "SecurePassword123"
    full_name = f"Resident {unique_suffix}"

    # 1. Register new user
    reg_payload = {
        "full_name": full_name,
        "email": test_email,
        "password": test_password,
        "confirm_password": test_password
    }
    reg_res = client.post("/auth/register", json=reg_payload)
    assert reg_res.status_code == 201, f"Registration failed: {reg_res.text}"
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == test_email
    assert reg_data["user"]["full_name"] == full_name
    assert reg_data["user"]["has_profile"] is False

    # 2. Prevent duplicate email registration
    dup_res = client.post("/auth/register", json=reg_payload)
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]

    # 3. Test login with wrong password
    bad_login_res = client.post("/auth/login", json={
        "email": test_email,
        "password": "WrongPassword!"
    })
    assert bad_login_res.status_code == 401

    # 4. Test login with correct credentials
    login_res = client.post("/auth/login", json={
        "email": test_email,
        "password": test_password
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    token = login_data["access_token"]
    assert token is not None

    # 5. Check /auth/me with bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == test_email


def test_household_profile_and_consumption_flow():
    """Verify household profile creation, update, electricity, and water submissions."""
    unique_suffix = int(time.time() * 1000) + 1
    test_email = f"profile_user_{unique_suffix}@example.com"
    test_password = "SecurePassword123"

    # Register
    reg_res = client.post("/auth/register", json={
        "full_name": "Eco Resident",
        "email": test_email,
        "password": test_password,
        "confirm_password": test_password
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify profile does not exist yet
    profile_check = client.get("/profile", headers=headers)
    assert profile_check.status_code == 404

    # Verify submitting consumption before profile creation fails
    elec_early = client.post("/consumption/electricity", headers=headers, json={"monthly_consumption_kwh": 250.0})
    assert elec_early.status_code == 400
    assert "household profile" in elec_early.json()["detail"].lower()

    # Create household profile
    profile_payload = {
        "household_members": 4,
        "house_type": "Apartment",
        "location": "Sector 62, Noida",
        "num_bathrooms": 2,
        "people_usually_at_home": 2,
        "unusual_occupancy": "None"
    }
    create_profile_res = client.post("/profile", headers=headers, json=profile_payload)
    assert create_profile_res.status_code == 201
    profile_data = create_profile_res.json()
    assert profile_data["household_members"] == 4
    assert profile_data["house_type"] == "Apartment"

    # Verify profile GET returns the created profile
    get_profile_res = client.get("/profile", headers=headers)
    assert get_profile_res.status_code == 200
    assert get_profile_res.json()["id"] == profile_data["id"]

    # Submit Electricity Consumption
    elec_payload = {
        "monthly_consumption_kwh": 345.5,
        "ac_count": 2,
        "fan_count": 4,
        "refrigerator_count": 1,
        "tv_count": 1,
        "geyser_count": 1,
        "washing_machine_count": 1,
        "water_pump_count": 1,
        "other_appliances": "Microwave, Air Fryer",
        "usage_notes": "AC used 6 hours/day during peak summer"
    }
    elec_res = client.post("/consumption/electricity", headers=headers, json=elec_payload)
    assert elec_res.status_code == 201
    elec_data = elec_res.json()
    assert elec_data["monthly_consumption_kwh"] == 345.5
    assert elec_data["ac_count"] == 2
    assert elec_data["profile_id"] == profile_data["id"]

    # Retrieve Electricity Records
    get_elec_res = client.get("/consumption/electricity", headers=headers)
    assert get_elec_res.status_code == 200
    assert len(get_elec_res.json()) >= 1
    assert get_elec_res.json()[0]["monthly_consumption_kwh"] == 345.5

    # Submit Water Consumption
    water_payload = {
        "monthly_consumption_litres": 12500.0,
        "num_showers": 4,
        "avg_shower_duration_mins": 8.5,
        "bucket_usage": 2,
        "washing_machine_usage": "3 cycles per week",
        "garden_watering": "Alternate days",
        "vehicle_washing": "Once a week",
        "water_pump_usage": "45 mins per day",
        "other_water_usage": "Balcony cleaning"
    }
    water_res = client.post("/consumption/water", headers=headers, json=water_payload)
    assert water_res.status_code == 201
    water_data = water_res.json()
    assert water_data["monthly_consumption_litres"] == 12500.0
    assert water_data["num_showers"] == 4
    assert water_data["profile_id"] == profile_data["id"]

    # Retrieve Water Records
    get_water_res = client.get("/consumption/water", headers=headers)
    assert get_water_res.status_code == 200
    assert len(get_water_res.json()) >= 1
    assert get_water_res.json()[0]["monthly_consumption_litres"] == 12500.0


def test_unauthorized_access_protection():
    """Verify protected endpoints reject requests without token or with invalid token."""
    res1 = client.get("/profile")
    assert res1.status_code == 401

    res2 = client.post("/consumption/electricity", json={"monthly_consumption_kwh": 100})
    assert res2.status_code == 401

    res3 = client.get("/consumption/water")
    assert res3.status_code == 401

    res4 = client.get("/profile", headers={"Authorization": "Bearer invalid_token_xyz"})
    assert res4.status_code == 401

    res5 = client.get("/consumption/summary")
    assert res5.status_code == 401


def test_consumption_summary_missing_profile():
    """Verify summary endpoint returns safe default response when user has no profile."""
    unique_suffix = int(time.time() * 1000) + 101
    email = f"summary_noprofile_{unique_suffix}@example.com"
    password = "TestPassword123!"

    reg_res = client.post("/auth/register", json={
        "full_name": "No Profile Resident",
        "email": email,
        "password": password,
        "confirm_password": password
    })
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/consumption/summary", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["has_profile"] is False
    assert data["profile"] is None
    assert data["electricity"]["latest_record"] is None
    assert data["electricity"]["per_person_kwh"] is None
    assert data["electricity"]["change_pct_vs_previous"] is None
    assert data["electricity"]["total_records_count"] == 0
    assert data["water"]["latest_record"] is None
    assert data["water"]["per_person_litres_monthly"] is None
    assert data["water"]["per_person_litres_daily"] is None
    assert data["water"]["change_pct_vs_previous"] is None
    assert data["water"]["total_records_count"] == 0
    assert data["recent_electricity_records"] == []
    assert data["recent_water_records"] == []


def test_consumption_summary_with_profile_no_records():
    """Verify summary returns household profile with safe null metrics when no consumption is recorded."""
    unique_suffix = int(time.time() * 1000) + 202
    email = f"summary_norecords_{unique_suffix}@example.com"
    password = "TestPassword123!"

    reg_res = client.post("/auth/register", json={
        "full_name": "Profile Only Resident",
        "email": email,
        "password": password,
        "confirm_password": password
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create profile with 4 members
    client.post("/profile", headers=headers, json={
        "household_members": 4,
        "house_type": "Apartment",
        "location": "Indirapuram, Ghaziabad",
        "num_bathrooms": 2,
        "people_usually_at_home": 2,
        "unusual_occupancy": "None"
    })

    res = client.get("/consumption/summary", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["has_profile"] is True
    assert data["profile"]["household_members"] == 4
    assert data["electricity"]["latest_record"] is None
    assert data["electricity"]["per_person_kwh"] is None
    assert data["electricity"]["change_pct_vs_previous"] is None
    assert data["electricity"]["total_records_count"] == 0
    assert data["water"]["latest_record"] is None
    assert data["water"]["per_person_litres_monthly"] is None
    assert data["water"]["per_person_litres_daily"] is None
    assert data["water"]["change_pct_vs_previous"] is None
    assert data["water"]["total_records_count"] == 0


def test_consumption_summary_calculation_accuracy_and_trends():
    """Verify per-person metrics, null change on single record, and exact month-over-month calculation on two records."""
    unique_suffix = int(time.time() * 1000) + 303
    email = f"summary_trends_{unique_suffix}@example.com"
    password = "TestPassword123!"

    reg_res = client.post("/auth/register", json={
        "full_name": "Trends Resident",
        "email": email,
        "password": password,
        "confirm_password": password
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Profile with 4 members
    client.post("/profile", headers=headers, json={
        "household_members": 4,
        "house_type": "Independent House",
        "location": "Whitefield, Bengaluru",
        "num_bathrooms": 3,
        "people_usually_at_home": 3,
        "unusual_occupancy": "None"
    })

    # 2. Record #1 (Baseline): Electricity 400.0 kWh, Water 12000.0 Litres
    client.post("/consumption/electricity", headers=headers, json={
        "monthly_consumption_kwh": 400.0,
        "ac_count": 2,
        "fan_count": 5
    })
    client.post("/consumption/water", headers=headers, json={
        "monthly_consumption_litres": 12000.0,
        "num_showers": 4
    })

    # Summary with single record:
    # per-person electricity = 400 / 4 = 100.0 kWh
    # per-person water monthly = 12000 / 4 = 3000.0 Litres
    # per-person water daily (LPCD) = 12000 / (4 * 30) = 100.0 LPCD
    # Comparison changes MUST be null because only 1 record exists.
    res1 = client.get("/consumption/summary", headers=headers)
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["electricity"]["latest_record"]["monthly_consumption_kwh"] == 400.0
    assert d1["electricity"]["per_person_kwh"] == 100.0
    assert d1["electricity"]["change_pct_vs_previous"] is None
    assert d1["electricity"]["change_kwh_vs_previous"] is None
    assert d1["electricity"]["total_records_count"] == 1

    assert d1["water"]["latest_record"]["monthly_consumption_litres"] == 12000.0
    assert d1["water"]["per_person_litres_monthly"] == 3000.0
    assert d1["water"]["per_person_litres_daily"] == 100.0
    assert d1["water"]["change_pct_vs_previous"] is None
    assert d1["water"]["change_litres_vs_previous"] is None
    assert d1["water"]["total_records_count"] == 1

    # Small pause to guarantee distinct sequential order
    time.sleep(0.05)

    # 3. Record #2: Electricity 500.0 kWh (+100 kWh, +25%), Water 9000.0 Litres (-3000 Litres, -25%)
    client.post("/consumption/electricity", headers=headers, json={
        "monthly_consumption_kwh": 500.0,
        "ac_count": 2,
        "fan_count": 5
    })
    client.post("/consumption/water", headers=headers, json={
        "monthly_consumption_litres": 9000.0,
        "num_showers": 4
    })

    res2 = client.get("/consumption/summary", headers=headers)
    assert res2.status_code == 200
    d2 = res2.json()

    # Electricity checks:
    # Latest: 500.0 kWh
    # Per person: 500 / 4 = 125.0 kWh
    # Change kwh: 500 - 400 = 100.0 kWh
    # Change pct: ((500 - 400) / 400) * 100 = 25.0%
    assert d2["electricity"]["latest_record"]["monthly_consumption_kwh"] == 500.0
    assert d2["electricity"]["per_person_kwh"] == 125.0
    assert d2["electricity"]["change_kwh_vs_previous"] == 100.0
    assert d2["electricity"]["change_pct_vs_previous"] == 25.0
    assert d2["electricity"]["total_records_count"] == 2
    assert len(d2["recent_electricity_records"]) == 2
    assert d2["recent_electricity_records"][0]["monthly_consumption_kwh"] == 500.0
    assert d2["recent_electricity_records"][1]["monthly_consumption_kwh"] == 400.0

    # Water checks:
    # Latest: 9000.0 Litres
    # Per person monthly: 9000 / 4 = 2250.0 Litres
    # Per person daily: 9000 / (4 * 30) = 75.0 LPCD
    # Change litres: 9000 - 12000 = -3000.0 Litres
    # Change pct: ((9000 - 12000) / 12000) * 100 = -25.0%
    assert d2["water"]["latest_record"]["monthly_consumption_litres"] == 9000.0
    assert d2["water"]["per_person_litres_monthly"] == 2250.0
    assert d2["water"]["per_person_litres_daily"] == 75.0
    assert d2["water"]["change_litres_vs_previous"] == -3000.0
    assert d2["water"]["change_pct_vs_previous"] == -25.0
    assert d2["water"]["total_records_count"] == 2
    assert len(d2["recent_water_records"]) == 2
    assert d2["recent_water_records"][0]["monthly_consumption_litres"] == 9000.0
    assert d2["recent_water_records"][1]["monthly_consumption_litres"] == 12000.0


def test_consumption_summary_zero_baseline_division_safety():
    """Verify that when previous consumption is 0, percentage change returns null rather than crashing with ZeroDivisionError."""
    unique_suffix = int(time.time() * 1000) + 404
    email = f"summary_zero_{unique_suffix}@example.com"
    password = "TestPassword123!"

    reg_res = client.post("/auth/register", json={
        "full_name": "Zero Baseline Resident",
        "email": email,
        "password": password,
        "confirm_password": password
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.post("/profile", headers=headers, json={
        "household_members": 2,
        "house_type": "Apartment",
        "location": "Jaipur, Rajasthan",
        "num_bathrooms": 1,
        "people_usually_at_home": 1,
        "unusual_occupancy": "Vacation"
    })

    # Record 1: 0 kWh and 0 Litres (vacation month)
    client.post("/consumption/electricity", headers=headers, json={"monthly_consumption_kwh": 0.0})
    client.post("/consumption/water", headers=headers, json={"monthly_consumption_litres": 0.0})

    time.sleep(0.05)

    # Record 2: 120 kWh and 3000 Litres (return from vacation)
    client.post("/consumption/electricity", headers=headers, json={"monthly_consumption_kwh": 120.0})
    client.post("/consumption/water", headers=headers, json={"monthly_consumption_litres": 3000.0})

    res = client.get("/consumption/summary", headers=headers)
    assert res.status_code == 200
    data = res.json()

    # Electricity: previous was 0, so change_pct must be None (not DivisionByZero)
    assert data["electricity"]["latest_record"]["monthly_consumption_kwh"] == 120.0
    assert data["electricity"]["per_person_kwh"] == 60.0  # 120 / 2
    assert data["electricity"]["change_kwh_vs_previous"] == 120.0
    assert data["electricity"]["change_pct_vs_previous"] is None

    # Water: previous was 0, so change_pct must be None
    assert data["water"]["latest_record"]["monthly_consumption_litres"] == 3000.0
    assert data["water"]["per_person_litres_monthly"] == 1500.0  # 3000 / 2
    assert data["water"]["per_person_litres_daily"] == 50.0  # 3000 / (2 * 30)
    assert data["water"]["change_litres_vs_previous"] == 3000.0
    assert data["water"]["change_pct_vs_previous"] is None


