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
