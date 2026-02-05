
from fastapi import APIRouter, HTTPException, Request
from schemas.async_prediction import AsyncPredictRequest

from loguru import logger
from services.async_prediction_service import async_predict as async_prediction_service


router = APIRouter()

@router.post("/async_predict")
async def async_predict(request: AsyncPredictRequest, fastapi_request: Request):
    try:
        
        logger.info(f"Запрос на модерацию: {request}")

        kafka_producer = fastapi_request.app.state.kafka_producer

        return await async_prediction_service(request, kafka_producer)        
    
    except Exception as e:
        logger.error(f"Внутренняя ошибка сервера при предсказании: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка сервера при предсказании."
        )