from typing import Dict, Any, Optional
from services.model_service import ModelService
from schemas.prediction import PredictionRequest, PredictionResponse
from loguru import logger


def predict(request: PredictionRequest) -> PredictionResponse:
    try:
        features = ModelService.extract_features(request.model_dump())
    
        is_violation, probability = ModelService.predict(features)
        
        logger.info(f"Результат предсказания: seller_id={request.seller_id}, item_id={request.item_id}, is_violation={is_violation}, probability={probability:.4f}")
        
        return PredictionResponse(
            is_violation=is_violation,
            probability=probability
        )
        
    except Exception as e:
        logger.error(f"Что-то пошло не так: {e}")
        raise e
