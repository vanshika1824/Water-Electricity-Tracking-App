import logging
from fastapi import APIRouter, Depends, HTTPException, status

from models.user import User
from schemas.ml import (
    ElectricityPredictionRequest,
    ElectricityPredictionResponse,
    WaterPredictionRequest,
    WaterPredictionResponse,
    MLModelStatusResponse,
)
from services.auth_service import get_current_user
from services.ml_prediction_service import (
    predict_electricity,
    predict_water,
    get_ml_status,
    InsufficientHistoryError,
    InvalidHistorySequenceError,
    UnsupportedWaterCategoryError,
    ModelArtifactNotFoundError,
)

logger = logging.getLogger("water-electricity-api.routes.ml")

router = APIRouter(prefix="/ml", tags=["Machine Learning Forecasting"])


@router.get("/status", response_model=MLModelStatusResponse)
def get_model_status():
    """
    Health check and capability inspection for backend ML prediction pipelines.
    Reports loaded models, supported benchmark entities, and minimum historical requirements.
    """
    try:
        return get_ml_status()
    except Exception as e:
        logger.error(f"Error querying ML model status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query ML model pipeline status."
        )


@router.post(
    "/predict/electricity",
    response_model=ElectricityPredictionResponse,
    status_code=status.HTTP_200_OK
)
def predict_daily_electricity(
    request: ElectricityPredictionRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Generate daily household electricity consumption forecast in kWh.
    
    Requirements:
    - User authentication via JWT Bearer token.
    - At least 30 consecutive calendar days of daily readings leading up to the target forecast date.
    - Daily readings must contain positive values without date gaps or duplicates.
    """
    try:
        return predict_electricity(
            readings=request.readings,
            target_date=request.target_date
        )
    except InsufficientHistoryError as e:
        logger.warning(f"Electricity prediction failed (insufficient history): {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InvalidHistorySequenceError as e:
        logger.warning(f"Electricity prediction failed (invalid history sequence): {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ModelArtifactNotFoundError as e:
        logger.error(f"Electricity model artifact missing on server: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Electricity prediction model is currently unavailable on the server."
        )
    except Exception as e:
        logger.error(f"Unexpected error during electricity forecasting: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the electricity forecast."
        )


@router.post(
    "/predict/water",
    response_model=WaterPredictionResponse,
    status_code=status.HTTP_200_OK
)
def predict_daily_water(
    request: WaterPredictionRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Generate daily apartment-level water consumption forecast in Litres.
    
    Requirements:
    - User authentication via JWT Bearer token.
    - At least 30 consecutive calendar days of daily readings leading up to the target forecast date.
    - Supported benchmark apartment ID from the HSB Living Lab study ('APT_001' through 'APT_028').
    
    Important Note:
    AquaWatt users cannot be arbitrarily mapped to Swedish Living Lab apartment IDs.
    Requests with unrecognized or uncalibrated household identifiers will be rejected with HTTP 422.
    """
    try:
        return predict_water(
            readings=request.readings,
            benchmark_apartment_id=request.benchmark_apartment_id,
            benchmark_cluster_name=request.benchmark_cluster_name,
            target_date=request.target_date
        )
    except UnsupportedWaterCategoryError as e:
        logger.warning(f"Water prediction failed (unsupported category): {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except InsufficientHistoryError as e:
        logger.warning(f"Water prediction failed (insufficient history): {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InvalidHistorySequenceError as e:
        logger.warning(f"Water prediction failed (invalid history sequence): {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ModelArtifactNotFoundError as e:
        logger.error(f"Water model artifact missing on server: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Water prediction model is currently unavailable on the server."
        )
    except Exception as e:
        logger.error(f"Unexpected error during water forecasting: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the water forecast."
        )

