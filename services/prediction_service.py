from typing import Dict, Any
from loguru import logger
from metrics import PREDICTION_ERRORS_TOTAL

from services.model_service import ModelService

from repositories.advertisements import AdvertisementRepository
from repositories.users import UserRepository

from schemas.simple_prediction import SimplePredictRequest
from schemas.prediction import PredictionRequest, PredictionResponse

from errors import ModelUninitialized, UserNotFoundError, AdvertisementNotFoundError, AdvertisementCreationError, UserNotCreationError


async def _perform_model_inference(data: Dict[str, Any]) -> PredictionResponse:
    try:
        is_violation, probability = ModelService.predict(data)
        
        logger.info(
            f"Результат предсказания: seller_id={data.get('seller_id')}, "
            f"item_id={data.get('item_id')}, is_violation={is_violation}, "
            f"probability={probability:.4f}"
        )
        
        return PredictionResponse(
            is_violation=is_violation,
            probability=probability
        )

    except ModelUninitialized as e:
        PREDICTION_ERRORS_TOTAL.labels(error_type=type(e).__name__).inc()
        raise e
    except Exception as e:
        logger.error(f"Ошибка при инференсе модели: {e}")
        PREDICTION_ERRORS_TOTAL.labels(error_type="general_exception").inc()
        raise e

async def predict(request: PredictionRequest) -> PredictionResponse:
    return await _perform_model_inference(request.model_dump())


async def simple_predict(request: SimplePredictRequest) -> PredictionResponse:
    ad_repo = AdvertisementRepository()
    
    cached_result = await ad_repo.check_cache(request.item_id)
    if cached_result:
        logger.info(f"Найден кэшированный результат для {request.item_id}")
        return cached_result

    try:
        advertisement = await ad_repo.get(request.item_id)
        
        user_repo = UserRepository()
        user = await user_repo.get(advertisement.seller_id)

        ad_data = advertisement.model_dump()
        user_data = user.model_dump()
        
        full_data = {**ad_data, **user_data}
        logger.info(f'Загружены данные из бд: {full_data}')
        
    except (UserNotFoundError, AdvertisementNotFoundError, AdvertisementCreationError, UserNotCreationError) as e:
        error_type = type(e).__name__
        PREDICTION_ERRORS_TOTAL.labels(error_type=error_type).inc()
        raise e

    response = await _perform_model_inference(full_data)

    await ad_repo.to_cache(
        item_id=request.item_id, 
        is_violation=response.is_violation, 
        probability=response.probability
    )
    
    return response