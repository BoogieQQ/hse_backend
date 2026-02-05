import uvicorn
import yaml

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

from routes.prediction import router as predict_router
from routes.simple_prediction import router as simple_prediction_router
from routes.async_prediction import router as async_prediction_router
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

app.include_router(predict_router)
app.include_router(simple_prediction_router)
app.include_router(async_prediction_router)



if __name__ == "__main__":
    uvicorn.run(app, host=CONFIG['app']['host'], port=CONFIG['app']['port'])