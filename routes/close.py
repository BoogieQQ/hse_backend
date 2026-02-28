
from fastapi import APIRouter, HTTPException
from schemas.simple_prediction import SimplePredictRequest

from loguru import logger
from errors import AdvertisementNotFoundError, UserNotFoundError, AdvertisementCreationError, UserNotCreationError
from services.close_service import close_advertisement as close_advertisement_service
from schemas.simple_prediction import Advertisement


close_router = APIRouter()

@close_router.post("/close/{item_id}", response_model=Advertisement)
async def close(item_id: int):
    try:
        
        logger.info(f"Запрос на закрытие объявления: {item_id}")

        closed_adv = await close_advertisement_service(item_id)
        
        logger.info(f'Объявление закрыто {item_id}')

        return closed_adv

    except AdvertisementNotFoundError as e:
        logger.error(f"Объявление не найдено!")
        raise HTTPException(
            status_code=404,
            detail=f"Объявление не найдено."
        )
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