import uvicorn
import yaml

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

from routes.prediction import router as predict_router
from services.model_service import ModelService

with open('config.yaml', 'r') as file:
    CONFIG = yaml.safe_load(file)

async def lifespan(app: FastAPI):
    logger.info("Запуск сервиса модели...")
    ModelService.init()
    logger.info("Сервис готов к работе!")
    
    yield
    
    logger.info("Остановка сервиса...")

app = FastAPI(lifespan=lifespan)

app.include_router(predict_router)

if __name__ == "__main__":
    uvicorn.run(app, host=CONFIG['app']['host'], port=CONFIG['app']['port'])