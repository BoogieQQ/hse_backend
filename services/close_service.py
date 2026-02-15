from fastapi import HTTPException
from loguru import logger
from repositories.advertisements import AdvertisementRepository
from schemas.simple_prediction import Advertisement

async def close_advertisement(item_id: int) -> Advertisement:

    try:
        logger.info(f"Запрос на удаление объявления для item_id: {item_id}")
        
        ad_repo = AdvertisementRepository()
        advertisement_exist = await ad_repo.exists(item_id)

        if not advertisement_exist:
            logger.error(f"Объявление {item_id} не найдено.")
            raise AdvertisementNotFoundError(detail=f"Объявление с ID {item_id} не найдено")

        logger.info(f"Объявление {item_id} найдено в БД. Удалениe...")
        closed_adv = await ad_repo.delete(item_id)

        return closed_adv

    except Exception as e:
        logger.error(f"Что-то пошло не так: {e}")
        raise e