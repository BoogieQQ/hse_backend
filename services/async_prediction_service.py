import uuid

from repositories.moderations import ModerationResultRepository
from repositories.advertisements import AdvertisementRepository
from fastapi import HTTPException

from schemas.async_prediction import AsyncPredictRequest, AsyncPredictResponse
from loguru import logger

async def async_predict(request: AsyncPredictRequest, kafka_producer=None) -> AsyncPredictResponse:
    try:
        ad_repo = AdvertisementRepository()
        advertisement_exist = await ad_repo.exists(request.item_id)

        if not advertisement_exist:
            logger.error(f"Объявление {request.item_id} не найдено: {e}")
            raise HTTPException(
                status_code=404,
                detail=f"Объявление с ID {request.item_id} не найдено"
            )
        
        logger.info(f"Объявление {request.item_id} найдено в БД")

        moderation_repo = ModerationResultRepository()
        moderation_exist = await moderation_repo.exists(request.item_id)

        if moderation_exist:
            existing_task = await moderation_repo.get(request.item_id)
            if existing_task.status == "pending":
                logger.warning(f"Задача модерации {existing_task.id} уже существует")
                return AsyncPredictResponse(
                    task_id=existing_task.id,
                    status=existing_task.status,
                    message="Moderation task already exists"
                )

        try:
            moderation_result = await moderation_repo.create(
                item_id=request.item_id,
                status="pending",
                is_violation=None,
                probability=None,
                error_message=None,
                processed_at=None,
                retry_count=0,
                max_retries=3 
            )
            logger.info(f"Создана запись модерации с ID: {moderation_result.id}")
        except Exception as e:
            logger.error(f"Ошибка создания записи модерации: {e}")
            raise e
        try:
            await kafka_producer.send_moderation_request(moderation_result.id)
        except Exception as e:
            logger.error(f"Ошибка отправки в Kafka: {e}")
        
        return AsyncPredictResponse(
            task_id=moderation_result.id,
            status="pending",
            message="Moderation request accepted"
        )
    except Exception as e:
        logger.error(f"Что-то пошло не так: {e}")
        raise e