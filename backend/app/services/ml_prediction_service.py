"""
AquaWatt Machine Learning Prediction Service.
Loads, validates, and serves predictions from trained scikit-learn pipelines:
- Electricity: Daily household energy forecasting (kWh) via regularized autoregression.
- Water: Daily apartment-level consumption forecasting (Litres) via Random Forest.
"""

import os
import logging
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

from schemas.ml import (
    DailyReadingInput,
    ElectricityPredictionResponse,
    WaterPredictionResponse,
    MLModelStatusResponse,
)

logger = logging.getLogger("water-electricity-api.ml-service")

# Resolve model directory relative to backend app
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
MODELS_DIR = os.path.join(BASE_DIR, "machine_learning", "models")

# Model filenames by environment configuration
MODEL_CONFIGS = {
    "deployment": {
        "electricity": "electricity_deployment_model.joblib",
        "water": "water_deployment_model.joblib",
    },
    "evaluation": {
        "electricity": "electricity_best_model.joblib",
        "water": "water_best_model.joblib",
    },
}

# Module-level model cache to avoid re-reading disk on every request
_cached_electricity_pipeline = None
_cached_water_pipeline = None
_active_electricity_artifact: Optional[str] = None
_active_water_artifact: Optional[str] = None


def get_model_environment() -> str:
    """
    Determine active model environment: 'deployment' (default) or 'evaluation'.
    Controlled via AQUAWATT_ML_MODEL_ENV or ML_MODEL_ENV environment variable.
    Defaults safely to 'deployment' if unset, empty, or unconfigured.
    """
    raw_env = os.getenv("AQUAWATT_ML_MODEL_ENV") or os.getenv("ML_MODEL_ENV") or "deployment"
    clean_env = raw_env.strip().lower()
    if clean_env in ["evaluation", "eval", "benchmark"]:
        return "evaluation"
    return "deployment"


def get_configured_model_filenames() -> Tuple[str, str]:
    """
    Resolve configured model filenames based on the active model environment.
    Returns (electricity_filename, water_filename).
    """
    env_mode = get_model_environment()
    cfg = MODEL_CONFIGS.get(env_mode, MODEL_CONFIGS["deployment"])
    return cfg["electricity"], cfg["water"]


def reset_model_cache():
    """Reset cached pipeline instances and active artifact names (useful for testing/config switching)."""
    global _cached_electricity_pipeline, _cached_water_pipeline, _active_electricity_artifact, _active_water_artifact
    _cached_electricity_pipeline = None
    _cached_water_pipeline = None
    _active_electricity_artifact = None
    _active_water_artifact = None

# 28 Supported benchmark apartments and their ground-truth living lab cluster assignments
SUPPORTED_WATER_APARTMENTS: Dict[str, str] = {
    "APT_001": "CL_H",
    "APT_002": "CL_F",
    "APT_003": "CL_C",
    "APT_004": "CL_D",
    "APT_005": "CL_A",
    "APT_006": "CL_I",
    "APT_007": "CL_G",
    "APT_008": "CL_G",
    "APT_009": "CL_H",
    "APT_010": "CL_H",
    "APT_011": "CL_G",
    "APT_012": "CL_B",
    "APT_013": "CL_B",
    "APT_014": "CL_B",
    "APT_015": "CL_G",
    "APT_016": "CL_B",
    "APT_017": "CL_E",
    "APT_018": "CL_B",
    "APT_019": "CL_D",
    "APT_020": "CL_G",
    "APT_021": "CL_G",
    "APT_022": "CL_H",
    "APT_023": "CL_B",
    "APT_024": "CL_D",
    "APT_025": "CL_D",
    "APT_026": "CL_H",
    "APT_027": "CL_D",
    "APT_028": "CL_D",
}


# ==============================================================================
# CUSTOM DOMAIN EXCEPTIONS
# ==============================================================================

class MLServiceError(Exception):
    """Base exception for ML service operations."""
    pass


class ModelArtifactNotFoundError(MLServiceError):
    """Raised when the specified model file is missing on disk."""
    pass


class InsufficientHistoryError(MLServiceError):
    """Raised when fewer than 30 consecutive days of history are supplied."""
    pass


class InvalidHistorySequenceError(MLServiceError):
    """Raised when historical dates contain gaps, duplicates, or invalid order."""
    pass


class UnsupportedWaterCategoryError(MLServiceError):
    """Raised when an unrecognized apartment category is passed to the water model."""
    pass


# ==============================================================================
# MODEL LOADER & CACHE HELPERS
# ==============================================================================

def get_electricity_pipeline(custom_path: Optional[str] = None):
    """
    Load or retrieve cached electricity prediction pipeline.
    Uses deployment configuration by default with safe fallback to evaluation artifact if missing.
    """
    global _cached_electricity_pipeline, _active_electricity_artifact
    
    if custom_path is not None:
        if not os.path.exists(custom_path):
            raise ModelArtifactNotFoundError(f"Electricity model artifact not found at: {custom_path}")
        return joblib.load(custom_path)

    if _cached_electricity_pipeline is None:
        ele_filename, _ = get_configured_model_filenames()
        target_path = os.path.join(MODELS_DIR, ele_filename)
        
        # Safe fallback: if configured deployment model is missing, fallback to best_model if present
        if not os.path.exists(target_path):
            fallback_filename = "electricity_best_model.joblib"
            fallback_path = os.path.join(MODELS_DIR, fallback_filename)
            if os.path.exists(fallback_path):
                logger.warning(
                    f"Configured electricity model '{ele_filename}' not found at {target_path}. "
                    f"Falling back to evaluation model '{fallback_filename}'."
                )
                target_path = fallback_path
                ele_filename = fallback_filename
            else:
                raise ModelArtifactNotFoundError(
                    f"Neither configured electricity artifact '{ele_filename}' nor fallback '{fallback_filename}' was found in {MODELS_DIR}."
                )
                
        logger.info(f"Loading electricity model pipeline from {target_path} (env={get_model_environment()})...")
        _cached_electricity_pipeline = joblib.load(target_path)
        _active_electricity_artifact = ele_filename
        logger.info(f"Electricity model ({ele_filename}) loaded successfully into memory.")
        
    return _cached_electricity_pipeline


def get_water_pipeline(custom_path: Optional[str] = None):
    """
    Load or retrieve cached water prediction pipeline.
    Uses deployment configuration by default with safe fallback to evaluation artifact if missing.
    """
    global _cached_water_pipeline, _active_water_artifact
    
    if custom_path is not None:
        if not os.path.exists(custom_path):
            raise ModelArtifactNotFoundError(f"Water model artifact not found at: {custom_path}")
        return joblib.load(custom_path)

    if _cached_water_pipeline is None:
        _, wat_filename = get_configured_model_filenames()
        target_path = os.path.join(MODELS_DIR, wat_filename)
        
        # Safe fallback: if configured deployment model is missing, fallback to best_model if present
        if not os.path.exists(target_path):
            fallback_filename = "water_best_model.joblib"
            fallback_path = os.path.join(MODELS_DIR, fallback_filename)
            if os.path.exists(fallback_path):
                logger.warning(
                    f"Configured water model '{wat_filename}' not found at {target_path}. "
                    f"Falling back to evaluation model '{fallback_filename}'."
                )
                target_path = fallback_path
                wat_filename = fallback_filename
            else:
                raise ModelArtifactNotFoundError(
                    f"Neither configured water artifact '{wat_filename}' nor fallback '{fallback_filename}' was found in {MODELS_DIR}."
                )
                
        logger.info(f"Loading water model pipeline from {target_path} (env={get_model_environment()})...")
        _cached_water_pipeline = joblib.load(target_path)
        _active_water_artifact = wat_filename
        logger.info(f"Water model ({wat_filename}) loaded successfully into memory.")
        
    return _cached_water_pipeline


def get_ml_status() -> MLModelStatusResponse:
    """Check health, active environment, and loaded status of both model pipelines."""
    env_mode = get_model_environment()
    cfg_ele, cfg_wat = get_configured_model_filenames()
    ele_filename = _active_electricity_artifact or cfg_ele
    wat_filename = _active_water_artifact or cfg_wat
    ele_path = os.path.join(MODELS_DIR, ele_filename)
    wat_path = os.path.join(MODELS_DIR, wat_filename)
    
    return MLModelStatusResponse(
        status="active",
        model_environment=env_mode,
        electricity_model_loaded=os.path.exists(ele_path),
        water_model_loaded=os.path.exists(wat_path),
        electricity_model_artifact=ele_filename,
        water_model_artifact=wat_filename,
        supported_water_apartments=sorted(list(SUPPORTED_WATER_APARTMENTS.keys())),
        minimum_history_days=30
    )


# ==============================================================================
# INPUT VALIDATION & FEATURE ENGINEERING
# ==============================================================================

def validate_and_extract_features(
    readings: List[DailyReadingInput],
    target_date: Optional[date] = None
) -> Tuple[Dict[str, float], date, int]:
    """
    Validates user consumption history and extracts autoregressive lag and rolling features.
    
    Requirements:
    1. At least 30 consecutive calendar days.
    2. No duplicate dates.
    3. No date gaps within the active 30-day window.
    4. Target date must equal (last_reading_date + 1 day).
    5. No negative consumption readings.
    """
    if len(readings) < 30:
        raise InsufficientHistoryError(
            f"At least 30 consecutive daily readings are required to extract autoregressive features (received {len(readings)})."
        )

    # 1. Check for negative consumption
    for r in readings:
        if r.consumption < 0:
            raise InvalidHistorySequenceError(f"Negative consumption reading ({r.consumption}) detected on {r.date}.")

    # 2. Check for duplicate dates
    date_list = [r.date for r in readings]
    if len(date_list) != len(set(date_list)):
        seen = set()
        duplicates = [d.isoformat() for d in date_list if d in seen or seen.add(d)]
        raise InvalidHistorySequenceError(
            f"Historical readings contain duplicate dates ({duplicates[:3]}). Each calendar day must appear exactly once."
        )

    # 3. Sort chronologically
    sorted_readings = sorted(readings, key=lambda x: x.date)
    
    # 4. Extract the active 30-day window ending at the most recent reading
    active_window = sorted_readings[-30:]
    last_date = active_window[-1].date
    
    # Verify strict calendar continuity (no gaps) across the 30-day window
    for i in range(1, len(active_window)):
        expected_prev = active_window[i].date - timedelta(days=1)
        actual_prev = active_window[i - 1].date
        if actual_prev != expected_prev:
            raise InvalidHistorySequenceError(
                f"Historical readings contain a date gap: missing calendar day between {actual_prev} and {active_window[i].date}. "
                "The feature extraction pipeline requires exactly 30 consecutive, unbroken calendar days."
            )

    # 5. Determine and validate prediction target date
    expected_target_date = last_date + timedelta(days=1)
    if target_date is not None:
        if target_date != expected_target_date:
            raise InvalidHistorySequenceError(
                f"Target prediction date {target_date} must be exactly one calendar day after the last recorded reading ({last_date}). "
                f"Expected: {expected_target_date}."
            )
        pred_date = target_date
    else:
        pred_date = expected_target_date

    # 6. Compute exact autoregressive lag and rolling features for pred_date
    # lag_1: day prior to pred_date (last_date)
    lag_1 = float(active_window[-1].consumption)
    # lag_7: 7 days prior to pred_date
    lag_7 = float(active_window[-7].consumption)
    # lag_30: 30 days prior to pred_date
    lag_30 = float(active_window[-30].consumption)

    # Rolling 7-day window: the 7 days prior to pred_date
    w7_values = [float(r.consumption) for r in active_window[-7:]]
    rolling_mean_7 = float(np.mean(w7_values))
    rolling_std_7 = float(np.std(w7_values, ddof=1)) if len(w7_values) > 1 else 0.0

    # Rolling 30-day window: the 30 days prior to pred_date
    w30_values = [float(r.consumption) for r in active_window]
    rolling_mean_30 = float(np.mean(w30_values))

    # Calendar features relative to target pred_date
    day_of_week = pred_date.weekday()  # 0 = Monday, 6 = Sunday
    is_weekend = 1 if day_of_week in [5, 6] else 0
    month = pred_date.month
    day_of_year = pred_date.timetuple().tm_yday

    features = {
        "lag_1": round(lag_1, 4),
        "lag_7": round(lag_7, 4),
        "lag_30": round(lag_30, 4),
        "rolling_mean_7": round(rolling_mean_7, 4),
        "rolling_std_7": round(rolling_std_7, 4),
        "rolling_mean_30": round(rolling_mean_30, 4),
        "day_of_week": day_of_week,
        "is_weekend": is_weekend,
        "month": month,
        "day_of_year": day_of_year,
    }

    return features, pred_date, len(sorted_readings)


# ==============================================================================
# INFERENCE ENGINES
# ==============================================================================

def predict_electricity(
    readings: List[DailyReadingInput],
    target_date: Optional[date] = None,
    custom_model_path: Optional[str] = None
) -> ElectricityPredictionResponse:
    """
    Generate daily electricity consumption prediction in kWh.
    """
    pipeline = get_electricity_pipeline(custom_path=custom_model_path)
    features, pred_date, history_len = validate_and_extract_features(readings, target_date=target_date)

    # Required column order for electricity pipeline
    feature_columns = [
        "lag_1", "lag_7", "lag_30",
        "rolling_mean_7", "rolling_std_7", "rolling_mean_30",
        "day_of_week", "is_weekend", "month", "day_of_year"
    ]
    input_df = pd.DataFrame([[features[c] for c in feature_columns]], columns=feature_columns)

    # Perform inference through scikit-learn pipeline (scaler + ridge)
    raw_pred = pipeline.predict(input_df)[0]
    predicted_kwh = max(0.0, float(raw_pred))

    model_name = type(pipeline.named_steps.get("ridge", pipeline)).__name__
    artifact_name = os.path.basename(custom_model_path) if custom_model_path else (_active_electricity_artifact or get_configured_model_filenames()[0])

    return ElectricityPredictionResponse(
        predicted_consumption_kwh=round(predicted_kwh, 2),
        prediction_date=pred_date,
        unit="kWh",
        model_name=f"Pipeline(StandardScaler, {model_name})",
        model_artifact=artifact_name,
        prediction_type="experimental_benchmark",
        history_days_used=history_len,
        features_summary=features,
        data_source="UCI Individual Household Electric Power Consumption Benchmark (France)",
        disclaimer=(
            "Experimental benchmark forecast for algorithm demonstration. "
            "Represents a single European household; not calibrated to urban Indian cooling/grid dynamics."
        )
    )


def predict_water(
    readings: List[DailyReadingInput],
    benchmark_apartment_id: str,
    benchmark_cluster_name: Optional[str] = None,
    target_date: Optional[date] = None,
    custom_model_path: Optional[str] = None
) -> WaterPredictionResponse:
    """
    Generate daily water consumption prediction in Litres.
    Requires a valid benchmark apartment ID ('APT_001' to 'APT_028').
    """
    # Validate apartment category against Swedish research benchmark registry
    clean_apt_id = benchmark_apartment_id.strip().upper()
    if clean_apt_id not in SUPPORTED_WATER_APARTMENTS:
        raise UnsupportedWaterCategoryError(
            f"Unsupported benchmark apartment ID '{benchmark_apartment_id}'. "
            "The trained model relies on categorical embeddings from the HSB Living Lab study (APT_001 through APT_028). "
            "AquaWatt households cannot be mapped to arbitrary Swedish living lab categories. "
            "Please provide a supported benchmark apartment ID."
        )

    # Resolve cluster name
    ground_truth_cluster = SUPPORTED_WATER_APARTMENTS[clean_apt_id]
    cluster = benchmark_cluster_name.strip().upper() if benchmark_cluster_name else ground_truth_cluster

    pipeline = get_water_pipeline(custom_path=custom_model_path)
    features, pred_date, history_len = validate_and_extract_features(readings, target_date=target_date)

    # Construct complete input DataFrame including categorical columns
    input_row = {**features, "apartment": clean_apt_id, "cluster_name": cluster}
    feature_columns = [
        "lag_1", "lag_7", "lag_30",
        "rolling_mean_7", "rolling_std_7", "rolling_mean_30",
        "day_of_week", "is_weekend", "month", "day_of_year",
        "apartment", "cluster_name"
    ]
    input_df = pd.DataFrame([[input_row[c] for c in feature_columns]], columns=feature_columns)

    # Perform inference through scikit-learn pipeline (ColumnTransformer + RandomForest)
    raw_pred = pipeline.predict(input_df)[0]
    predicted_litres = max(0.0, float(raw_pred))

    model_name = type(pipeline.named_steps.get("rf", pipeline)).__name__
    artifact_name = os.path.basename(custom_model_path) if custom_model_path else (_active_water_artifact or get_configured_model_filenames()[1])

    return WaterPredictionResponse(
        predicted_consumption_litres=round(predicted_litres, 1),
        prediction_date=pred_date,
        unit="Litres",
        model_name=f"Pipeline(ColumnTransformer, {model_name})",
        model_artifact=artifact_name,
        prediction_type="experimental_benchmark",
        benchmark_apartment_id=clean_apt_id,
        benchmark_cluster_name=cluster,
        history_days_used=history_len,
        features_summary=features,
        data_source="HSB Living Lab Fixture-Level Benchmark (Chalmers University, Sweden)",
        disclaimer=(
            "Experimental benchmark forecast for algorithm demonstration. "
            "Trained on Swedish living lab residential units with 24/7 municipal supply; "
            "not calibrated to Indian intermittent water sumps/tanks."
        )
    )

