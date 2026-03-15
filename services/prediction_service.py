from typing import Dict, Any, Optional
from services.model_service import ModelService
from schemas.prediction import PredictionRequest, PredictionResponse
from loguru import logger
from metrics import PREDICTION_ERRORS_TOTAL
from errors import ModelUninitialized


def predict(request: PredictionRequest) -> PredictionResponse:
    try:    
        request = request.model_dump()
        
        is_violation, probability = ModelService.predict(request)
        
        logger.info(f"Результат предсказания: seller_id={request['seller_id']}, item_id={request['item_id']}, is_violation={is_violation}, probability={probability:.4f}")
        
        return PredictionResponse(
            is_violation=is_violation,
            probability=probability
        )
    except ModelUninitialized as e:
        error_type = type(e).__name__
        PREDICTION_ERRORS_TOTAL.labels(error_type=error_type).inc()
        raise
    except Exception as e:
        logger.error(f"Что-то пошло не так: {e}")
        PREDICTION_ERRORS_TOTAL.labels(error_type="general_exception").inc()
        raise e
