import json
import yaml
from aiokafka import AIOKafkaProducer
from datetime import datetime
from aiokafka.errors import KafkaError
from loguru import logger

with open('config.yaml', 'r') as file:
    CONFIG = yaml.safe_load(file)

class KafkaProducer:
    def __init__(self, bootstrap_servers: str):
        self._bootstrap = bootstrap_servers
        self._producer = None  # AIOKafkaProducer

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(bootstrap_servers=self._bootstrap)
        await self._producer.start()

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()

    async def send_moderation_request(self, item_id: int):
        if not self._producer:
            raise RuntimeError("Producer не инициализирован.")

        message = {
            "item_id": item_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            await self._producer.send_and_wait(
                topic=CONFIG['kafka']['moderation_topic'],
                value=json.dumps(message).encode('utf-8')
            )

        except KafkaError as e:
            logger.info(f"Ошибка отправки в топик moderation Кафки: {e}")
            raise e