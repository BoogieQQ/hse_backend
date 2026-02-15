from typing import Dict, Any, Optional
from repositories.advertisements import AdvertisementRepository
from repositories.users import UserRepository
from schemas.simple_prediction import SimplePredictRequest
from schemas.prediction import PredictionResponse
from errors import AdvertisementNotFoundError, UserNotFoundError, AdvertisementCreationError, UserNotCreationError

from services.model_service import ModelService
from loguru import logger
from fastapi import HTTPException

from asyncpg.exceptions import ForeignKeyViolationError


async def simple_predict(request: SimplePredictRequest) -> PredictionResponse:
    try:
        ad_repo = AdvertisementRepository()

        cached_result = await ad_repo.check_cache(request.item_id)
        if cached_result:
            logger.info(f"Найден кэшированный результат модерации для объявления {request.item_id}")

            return cached_result
        
        advertisement = await ad_repo.get(request.item_id)
        
        user_repo = UserRepository()
        user = await user_repo.get(advertisement.seller_id)

        ad_data = advertisement.model_dump()
        user_data = user.model_dump()
        request = {**ad_data, **user_data}
        logger.info(f'Загружены данные из бд: {request}')

        features = ModelService.extract_features(request)
    
        is_violation, probability = ModelService.predict(features)
        
        logger.info(f"Результат предсказания: seller_id={request['seller_id']}, item_id={request['item_id']}, is_violation={is_violation}, probability={probability:.4f}")
        
        await ad_repo.to_cache(item_id=request['item_id'], is_violation=is_violation, probability=probability)

        return PredictionResponse(
            is_violation=is_violation,
            probability=probability
        )
    
    except (UserNotFoundError, AdvertisementNotFoundError, AdvertisementCreationError, UserNotCreationError) as e:
        raise
    except Exception as e:
        logger.error(f"Что-то пошло не так: {e}")
        raise e
