from fastapi import APIRouter, HTTPException
from services.prediction_service import predict as prediction_service_predict
from schemas.prediction import PredictionRequest, PredictionResponse
from services.model_service import ModelService
from dependencies import CurrentUserRequired
from errors import ModelUninitialized

from loguru import logger

prediction_router = APIRouter()

@prediction_router.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest, current_user: CurrentUserRequired):
    try:
        logger.info(f"Запрос на предсказание: {request}")

        response = await prediction_service_predict(request)
        
        return response

    except ModelUninitialized as e:
        logger.error("Модель не загружена при попытке предсказания")
    
    except ValueError as e:
        logger.error(f"Ошибка валидации входных данных: {e}")

        raise HTTPException(
            status_code=422,
            detail=f"Ошибка валидации входных данных: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Внутренняя ошибка сервера при предсказании: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка сервера при предсказании."
        )