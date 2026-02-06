from fastapi import HTTPException
from loguru import logger
from repositories.moderations import ModerationResultRepository
from schemas.async_prediction import ModerationResult
from typing import Optional
from errors import ModerationResultNotFoundError

async def get_moderation_result(task_id: int) -> ModerationResult:

    try:
        logger.info(f"Запрос результата модерации для task_id: {task_id}")
        
        moderation_repo = ModerationResultRepository()
        
        task_exist = await moderation_repo.exists(task_id)

        if not task_exist:
            logger.error(f"Задача модерации с ID {task_id} не найдена")
            raise ModerationResultNotFoundError(f"Задача модерации с ID {task_id} не найдена")

        moderation_record = await moderation_repo.get(task_id)
        
        logger.info(f"Найдена задача модерации: {moderation_record}")
        
        return ModerationResult(
            id=moderation_record.id,
            **moderation_record.dict(exclude={'id'})
        )

    except Exception as e:
        logger.error(f"Что-то пошло не так: {e}")
        raise e