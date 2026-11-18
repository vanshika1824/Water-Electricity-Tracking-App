"""
AquaWatt Phase 5: Machine Learning Integration Tests.
Verifies endpoints, authentication, validation, error handling, and model inference:
- Successful electricity prediction.
- Successful water prediction where supported.
- Insufficient historical data (< 30 days).
- Missing dates (date gaps in 30-day window).
- Duplicate dates.
- Invalid consumption values (negative readings).
- Unsupported water categories.
- Missing model artifacts handling.
- Authentication requirements.
- Model input feature compatibility.
"""

import os
import sys
import time
from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient

# Ensure backend app is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))

from main import app
from services.ml_prediction_service import (
    validate_and_extract_features,
    get_electricity_pipeline,
    get_water_pipeline,
    predict_electricity,
    predict_water,
    get_model_environment,
    get_configured_model_filenames,
    reset_model_cache,
    MODELS_DIR,
    InsufficientHistoryError,
    InvalidHistorySequenceError,
    UnsupportedWaterCategoryError,
    ModelArtifactNotFoundError,
)
from schemas.ml import DailyReadingInput

client = TestClient(app)


def get_auth_token_for_test_user() -> str:
    """Helper to register and log in a fresh user and retrieve JWT token."""
    unique_suffix = int(time.time() * 1000)
    email = f"ml_test_{unique_suffix}@example.com"
    password = "TestPassword123!"
    
    # Register
    reg_resp = client.post("/auth/register", json={
        "full_name": f"ML Tester {unique_suffix}",
        "email": email,
        "password": password,
        "confirm_password": password
    })
    assert reg_resp.status_code == 201, f"Registration failed: {reg_resp.text}"
    
    # Login
    login_resp = client.post("/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    return login_resp.json()["access_token"]


def generate_consecutive_readings(days: int = 35, start_date: date = date(2026, 9, 1), base_val: float = 25.0):
    """Generate clean consecutive daily consumption readings."""
    readings = []
    for i in range(days):
        d = start_date + timedelta(days=i)
        val = base_val + (i % 7) * 1.5
        readings.append({"date": d.isoformat(), "consumption": round(val, 2)})
    return readings


# ==============================================================================
# 1. STATUS & CAPABILITY ENDPOINT
# ==============================================================================

def test_ml_status_endpoint():
    """Verify GET /ml/status returns operational status and supported categories."""
    response = client.get("/ml/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["electricity_model_loaded"] is True
    assert data["water_model_loaded"] is True
    assert "APT_001" in data["supported_water_apartments"]
    assert "APT_028" in data["supported_water_apartments"]
    assert len(data["supported_water_apartments"]) == 28
    assert data["minimum_history_days"] == 30


# ==============================================================================
# 2. AUTHENTICATION REQUIREMENTS
# ==============================================================================

def test_electricity_prediction_unauthorized():
    """Verify POST /ml/predict/electricity rejects unauthenticated requests with 401."""
    payload = {"readings": generate_consecutive_readings(35)}
    response = client.post("/ml/predict/electricity", json=payload)
    assert response.status_code == 401


def test_water_prediction_unauthorized():
    """Verify POST /ml/predict/water rejects unauthenticated requests with 401."""
    payload = {
        "readings": generate_consecutive_readings(35),
        "benchmark_apartment_id": "APT_001"
    }
    response = client.post("/ml/predict/water", json=payload)
    assert response.status_code == 401


# ==============================================================================
# 3. SUCCESSFUL PREDICTIONS
# ==============================================================================

def test_successful_electricity_prediction():
    """Verify valid authenticated electricity prediction returns correct forecast in kWh."""
    token = get_auth_token_for_test_user()
    readings = generate_consecutive_readings(35, start_date=date(2026, 9, 1), base_val=22.5)
    
    response = client.post(
        "/ml/predict/electricity",
        headers={"Authorization": f"Bearer {token}"},
        json={"readings": readings}
    )
    assert response.status_code == 200
    data = response.json()
    
    assert "predicted_consumption_kwh" in data
    assert data["predicted_consumption_kwh"] > 0
    assert data["unit"] == "kWh"
    assert data["prediction_date"] == "2026-10-06"  # Day after Sept 1 + 34 days = Oct 5
    assert data["prediction_type"] == "experimental_benchmark"
    assert "UCI" in data["data_source"]
    assert "features_summary" in data
    assert "lag_1" in data["features_summary"]
    assert "rolling_mean_7" in data["features_summary"]
    assert "rolling_mean_30" in data["features_summary"]


def test_successful_water_prediction_supported_category():
    """Verify valid authenticated water prediction for supported benchmark apartment."""
    token = get_auth_token_for_test_user()
    readings = generate_consecutive_readings(35, start_date=date(2026, 9, 1), base_val=75.0)
    
    response = client.post(
        "/ml/predict/water",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "readings": readings,
            "benchmark_apartment_id": "APT_001"
        }
    )
    assert response.status_code == 200
    data = response.json()
    
    assert "predicted_consumption_litres" in data
    assert data["predicted_consumption_litres"] > 0
    assert data["unit"] == "Litres"
    assert data["prediction_date"] == "2026-10-06"
    assert data["benchmark_apartment_id"] == "APT_001"
    assert data["benchmark_cluster_name"] == "CL_H"  # Auto-resolved ground-truth cluster
    assert data["prediction_type"] == "experimental_benchmark"
    assert "HSB Living Lab" in data["data_source"]


# ==============================================================================
# 4. INPUT VALIDATION & ERROR HANDLING
# ==============================================================================

def test_insufficient_historical_data():
    """Verify requests with fewer than 30 readings are rejected with 422 or 400."""
    token = get_auth_token_for_test_user()
    short_readings = generate_consecutive_readings(25)  # only 25 days
    
    response = client.post(
        "/ml/predict/electricity",
        headers={"Authorization": f"Bearer {token}"},
        json={"readings": short_readings}
    )
    assert response.status_code == 422  # Pydantic min_length=30 validation


def test_missing_dates_gap_in_history():
    """Verify history with a missing calendar day (gap) is rejected with 400."""
    token = get_auth_token_for_test_user()
    readings = generate_consecutive_readings(32, start_date=date(2026, 9, 1))
    
    # Introduce a 2-day gap by dropping reading at index 15
    readings_with_gap = readings[:15] + readings[17:]
    
    response = client.post(
        "/ml/predict/electricity",
        headers={"Authorization": f"Bearer {token}"},
        json={"readings": readings_with_gap}
    )
    assert response.status_code == 400
    assert "date gap" in response.json()["detail"].lower()


def test_duplicate_dates_in_history():
    """Verify history with duplicate dates is rejected with 400."""
    token = get_auth_token_for_test_user()
    readings = generate_consecutive_readings(31, start_date=date(2026, 9, 1))
    
    # Duplicate the last reading's date
    readings.append({"date": readings[-1]["date"], "consumption": 30.0})
    
    response = client.post(
        "/ml/predict/electricity",
        headers={"Authorization": f"Bearer {token}"},
        json={"readings": readings}
    )
    assert response.status_code == 400
    assert "duplicate" in response.json()["detail"].lower()


def test_invalid_negative_consumption_values():
    """Verify negative consumption readings are rejected with 422."""
    token = get_auth_token_for_test_user()
    readings = generate_consecutive_readings(30)
    readings[5]["consumption"] = -12.5  # Negative value
    
    response = client.post(
        "/ml/predict/electricity",
        headers={"Authorization": f"Bearer {token}"},
        json={"readings": readings}
    )
    assert response.status_code == 422


def test_unsupported_water_category():
    """Verify request with an unsupported/unknown apartment category is rejected with 422."""
    token = get_auth_token_for_test_user()
    readings = generate_consecutive_readings(35)
    
    response = client.post(
        "/ml/predict/water",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "readings": readings,
            "benchmark_apartment_id": "APT_999"  # Non-existent in Swedish benchmark
        }
    )
    assert response.status_code == 422
    assert "unsupported" in response.json()["detail"].lower()
    assert "hsb living lab" in response.json()["detail"].lower()


# ==============================================================================
# 5. MODEL ARTIFACT & FEATURE COMPATIBILITY
# ==============================================================================

def test_missing_model_artifact_handling():
    """Verify attempting to load a missing model file raises ModelArtifactNotFoundError."""
    dummy_readings = [DailyReadingInput(date=date(2026, 1, 1) + timedelta(days=i), consumption=20.0) for i in range(35)]
    
    with pytest.raises(ModelArtifactNotFoundError):
        predict_electricity(
            readings=dummy_readings,
            custom_model_path="non_existent_electricity_model.joblib"
        )


def test_model_input_feature_compatibility():
    """Verify that extracted features exactly match the trained scikit-learn pipeline schemas."""
    dummy_readings = [DailyReadingInput(date=date(2026, 1, 1) + timedelta(days=i), consumption=15.0 + i) for i in range(35)]
    features, pred_date, n_days = validate_and_extract_features(dummy_readings)
    
    ele_pipeline = get_electricity_pipeline()
    wat_pipeline = get_water_pipeline()
    
    # Check electricity pipeline feature compatibility
    ele_features_expected = [
        "lag_1", "lag_7", "lag_30",
        "rolling_mean_7", "rolling_std_7", "rolling_mean_30",
        "day_of_week", "is_weekend", "month", "day_of_year"
    ]
    import pandas as pd
    ele_input = pd.DataFrame([[features[c] for c in ele_features_expected]], columns=ele_features_expected)
    ele_pred = ele_pipeline.predict(ele_input)
    assert len(ele_pred) == 1
    assert ele_pred[0] > 0
    
    # Check water pipeline feature compatibility
    wat_features_expected = ele_features_expected + ["apartment", "cluster_name"]
    wat_row = {**features, "apartment": "APT_001", "cluster_name": "CL_H"}
    wat_input = pd.DataFrame([[wat_row[c] for c in wat_features_expected]], columns=wat_features_expected)
    wat_pred = wat_pipeline.predict(wat_input)
    assert len(wat_pred) == 1
    assert wat_pred[0] > 0


# ==============================================================================
# 6. MODEL ARTIFACT CONFIGURATION & ENVIRONMENT SELECTION
# ==============================================================================

def test_default_model_environment_is_deployment():
    """Verify default environment is 'deployment' and loads deployment artifacts."""
    reset_model_cache()
    assert get_model_environment() == "deployment"
    ele_file, wat_file = get_configured_model_filenames()
    assert ele_file == "electricity_deployment_model.joblib"
    assert wat_file == "water_deployment_model.joblib"

    # Status endpoint reflects deployment configuration
    response = client.get("/ml/status")
    assert response.status_code == 200
    status_data = response.json()
    assert status_data["model_environment"] == "deployment"
    assert status_data["electricity_model_artifact"] == "electricity_deployment_model.joblib"
    assert status_data["water_model_artifact"] == "water_deployment_model.joblib"

    # Verify inference uses deployment model artifacts
    token = get_auth_token_for_test_user()
    readings = generate_consecutive_readings(35)

    ele_resp = client.post(
        "/ml/predict/electricity",
        headers={"Authorization": f"Bearer {token}"},
        json={"readings": readings}
    )
    assert ele_resp.status_code == 200
    assert ele_resp.json()["model_artifact"] == "electricity_deployment_model.joblib"

    wat_resp = client.post(
        "/ml/predict/water",
        headers={"Authorization": f"Bearer {token}"},
        json={"readings": readings, "benchmark_apartment_id": "APT_001"}
    )
    assert wat_resp.status_code == 200
    assert wat_resp.json()["model_artifact"] == "water_deployment_model.joblib"


def test_evaluation_model_environment_selection(monkeypatch):
    """Verify setting AQUAWATT_ML_MODEL_ENV='evaluation' switches to best_model artifacts."""
    monkeypatch.setenv("AQUAWATT_ML_MODEL_ENV", "evaluation")
    reset_model_cache()
    try:
        assert get_model_environment() == "evaluation"
        ele_file, wat_file = get_configured_model_filenames()
        assert ele_file == "electricity_best_model.joblib"
        assert wat_file == "water_best_model.joblib"

        response = client.get("/ml/status")
        assert response.status_code == 200
        status_data = response.json()
        assert status_data["model_environment"] == "evaluation"
        assert status_data["electricity_model_artifact"] == "electricity_best_model.joblib"
        assert status_data["water_model_artifact"] == "water_best_model.joblib"

        token = get_auth_token_for_test_user()
        readings = generate_consecutive_readings(35)

        ele_resp = client.post(
            "/ml/predict/electricity",
            headers={"Authorization": f"Bearer {token}"},
            json={"readings": readings}
        )
        assert ele_resp.status_code == 200
        assert ele_resp.json()["model_artifact"] == "electricity_best_model.joblib"

        wat_resp = client.post(
            "/ml/predict/water",
            headers={"Authorization": f"Bearer {token}"},
            json={"readings": readings, "benchmark_apartment_id": "APT_001"}
        )
        assert wat_resp.status_code == 200
        assert wat_resp.json()["model_artifact"] == "water_best_model.joblib"
    finally:
        monkeypatch.delenv("AQUAWATT_ML_MODEL_ENV", raising=False)
        reset_model_cache()


def test_graceful_fallback_when_deployment_model_missing(monkeypatch):
    """Verify that when deployment model is missing, the service safely falls back to evaluation model."""
    import services.ml_prediction_service as ml_mod
    monkeypatch.setattr(
        ml_mod,
        "get_configured_model_filenames",
        lambda: ("nonexistent_electricity_deployment.joblib", "nonexistent_water_deployment.joblib")
    )
    reset_model_cache()
    try:
        # Should log warning and fall back to best_model without raising error
        ele_pipe = get_electricity_pipeline()
        assert ele_pipe is not None
        assert ml_mod._active_electricity_artifact == "electricity_best_model.joblib"

        wat_pipe = get_water_pipeline()
        assert wat_pipe is not None
        assert ml_mod._active_water_artifact == "water_best_model.joblib"
    finally:
        reset_model_cache()


def test_missing_both_configured_and_fallback_models_raises_error(monkeypatch, tmp_path):
    """Verify ModelArtifactNotFoundError is raised if neither configured nor fallback model exists."""
    import services.ml_prediction_service as ml_mod
    monkeypatch.setattr(ml_mod, "MODELS_DIR", str(tmp_path))
    reset_model_cache()
    try:
        with pytest.raises(ModelArtifactNotFoundError) as exc_ele:
            get_electricity_pipeline()
        assert "Neither configured electricity artifact" in str(exc_ele.value)

        with pytest.raises(ModelArtifactNotFoundError) as exc_wat:
            get_water_pipeline()
        assert "Neither configured water artifact" in str(exc_wat.value)
    finally:
        reset_model_cache()


