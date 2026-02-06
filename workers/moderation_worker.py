import asyncio
import json
import yaml

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from loguru import logger
from services.model_service import ModelService

from repositories.advertisements import AdvertisementRepository
from repositories.users import UserRepository
from repositories.moderations import ModerationResultRepository

from errors import AdvertisementNotFoundError

import asyncpg

with open('config.yaml', 'r') as f:
    CONFIG = yaml.safe_load(f)


async def main():
    kafka_config = CONFIG['kafka']
    db_config    = CONFIG['database']
    
    max_retries = kafka_config['retries_before_dql']
    max_retry_delay = kafka_config['max_retry_delay']

    logger.info("Создание консумера и продюсера...")
    consumer = AIOKafkaConsumer(
        kafka_config['moderation_topic'],
        bootstrap_servers=kafka_config['bootstrap_servers'],
        group_id=kafka_config['moderation_consumer_group'],
        enable_auto_commit=False,
        auto_offset_reset='earliest'
    )
    
    producer = AIOKafkaProducer(
        bootstrap_servers=kafka_config['bootstrap_servers']
    )
    await producer.start()
    await consumer.start()

    logger.info("Запуск сервиса модели...")
    ModelService.init()
    logger.info("Сервис готов к работе!")

    logger.info(f"[Мoderation_worker] Обработка топика {kafka_config['moderation_topic']}")
    
    try:
        async for msg in consumer:
            for retry in range(1, max_retries+1):
                try:
                    message = msg.value
                    task_id = json.loads(message.decode('utf-8'))['item_id']
                    
                    logger.info(f'Обработка объявления task_id={task_id}')
                    
                    moderations_repo = ModerationResultRepository()

                    moderation_task = await moderations_repo.get(task_id)

                    item_id = moderation_task.item_id

                    ad_repo = AdvertisementRepository()

                    exists = await ad_repo.exists(item_id)
                    
                    if not exists:
                        logger.error(f'Объявление {item_id} не найдено.')
                        raise AdvertisementNotFoundError(f'Объявление {item_id} не найдено.')
                    
                    logger.info(f'Объявление {item_id} успешно найдено.')

                    advertisement = await ad_repo.get(item_id)
                    
                    user_repo = UserRepository()
                    user = await user_repo.get(advertisement.seller_id)

                    ad_data = advertisement.model_dump()
                    user_data = user.model_dump()
                    request = {**ad_data, **user_data}
                    logger.info(f'Загружены данные из бд: {request}')

                    features = ModelService.extract_features(request)
                
                    is_violation, probability = ModelService.predict(features)
                    
                    logger.info(f"Результат предсказания: seller_id={request['seller_id']}, item_id={request['item_id']}, is_violation={is_violation}, probability={probability:.4f}")

                    await moderations_repo.update(task_id=task_id, status='completed', is_violation=is_violation, probability=probability)
                    
                    logger.info(f'Обновлено: item_id={item_id}, violation={is_violation}')

                    await consumer.commit()

                    break # Выход из retry бока
                    
                except Exception as e:
                    delay = min(2 ** retry, max_retry_delay) # не более max_retry_delay секунд
                    logger.warning(f"Попытка {retry}/{max_retries} провалилась.")

                    if retry == max_retries:
                        try:
                        
                            logger.error(f"Все {max_retries} попыток провалились. Отправка в DLQ")

                            dlq_message = {
                                'item_id': item_id,
                                'error': f'All retries failed: {e}',
                                'original_message': message.decode('utf-8')
                            }
                            
                            await producer.send_and_wait(
                                kafka_config['moderation_dlq_topic'],
                                json.dumps(dlq_message).encode('utf-8')
                            )
                            await consumer.commit()
                            logger.info(f'Сообщение отправлено в DLQ после {max_retries} неудачных попыток.')

                            await moderations_repo.update_failed(task_id=task_id, status='failed', error_message=str(e))


                        except Exception as e:
                            logger.error(f'Ошибка во время отправки в dlq: {e}')
                    else:
                        logger.warning(f"Следующая попытка через {delay}с. Ошибка {e}")
                        await asyncio.sleep(delay)

    except Exception as e:
        logger.error(f"Непредвиденная ошибка в обработчике: {e}")
    finally:
        logger.info("Остановка consumer и producer...")
        await consumer.stop()
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(main())