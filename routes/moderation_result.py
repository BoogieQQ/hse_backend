from fastapi import APIRouter, HTTPException, Path
from loguru import logger
from schemas.async_prediction import ModerationResult
from services.moderation_result_service import get_moderation_result as get_moderation_result_service
from errors import ModerationResultNotFoundError

moderation_result_router = APIRouter()

@moderation_result_router.get("/moderation_result/{task_id}", response_model=ModerationResult)
async def get_moderation_result(task_id: int):

    try:
        logger.info(f"Получен запрос на результат модерации для task_id: {task_id}")
        
        result = await get_moderation_result_service(task_id)
        
        logger.info(f"Получен результат для task_id {task_id}: статус={result.status}")
        return result
        
    except ModerationResultNotFoundError as e:
        logger.warning(f"Задача модерации с ID {task_id} не найдена")
        raise HTTPException(
            status_code=404,
            detail=f"Задача модерации с ID {task_id} не найдена"
        )
    except Exception as e:
        logger.error(f"Неожиданная ошибка при обработке запроса для task_id {task_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Внутренняя ошибка сервера"
        )