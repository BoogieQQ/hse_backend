import uvicorn
import yaml

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

from routes.prediction import prediction_router
from routes.simple_prediction import simple_prediction_router
from routes.async_prediction import async_prediction_router
from routes.moderation_result import moderation_result_router 
from routes.close import close_router

from services.model_service import ModelService
from clients.kafka import KafkaProducer

with open('config.yaml', 'r') as file:
    CONFIG = yaml.safe_load(file)

async def lifespan(app: FastAPI):
    kafka_producer = KafkaProducer(CONFIG['kafka']['bootstrap_servers'])
    await kafka_producer.start()
    app.state.kafka_producer = kafka_producer

    logger.info("Запуск сервиса модели...")
    ModelService.init()
    logger.info("Сервис готов к работе!")
    
    yield
    
    logger.info("Остановка сервиса...")


app = FastAPI(lifespan=lifespan)

app.include_router(prediction_router)
app.include_router(simple_prediction_router)
app.include_router(async_prediction_router)
app.include_router(moderation_result_router)
app.include_router(close_router)

if __name__ == "__main__":
    uvicorn.run(app, host=CONFIG['app']['host'], port=CONFIG['app']['port'])