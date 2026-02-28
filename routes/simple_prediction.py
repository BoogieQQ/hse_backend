
from fastapi import APIRouter, HTTPException
from schemas.simple_prediction import SimplePredictRequest

from loguru import logger
from services.simple_prediction_service import simple_predict as simple_prediction_service
from errors import AdvertisementNotFoundError, UserNotFoundError, AdvertisementCreationError, UserNotCreationError


simple_prediction_router = APIRouter()

@simple_prediction_router.post("/simple_predict")
async def simple_predict(request: SimplePredictRequest):
    try:
        
        logger.info(f"Запрос на предсказание: {request}")

        response = await simple_prediction_service(request)
        
        logger.info(f'Успешно, результат предсказания: {response}')

        return response
    
    except UserNotFoundError as e:
        logger.error(f"Пользователь не найден!")
        raise HTTPException(
            status_code=404,
            detail=f"Пользователь не найден."
        )
    except AdvertisementNotFoundError as e:
        logger.error(f"Объявление не найдено!")
        raise HTTPException(
            status_code=404,
            detail=f"Объявление не найдено."
        )
    except AdvertisementCreationError as e:
        logger.error(f"Не удалось создать объявление!")
        raise HTTPException(
            status_code=400,
            detail=f"Ошибка при создании объявления."
        )
    except UserNotCreationError as e:
        logger.error(f"Не удалось создать пользователя!")
        raise HTTPException(
            status_code=400,
            detail=f"Ошибка при созадании пользователя."
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