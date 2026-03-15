import os
import time
import numpy as np
import yaml

from typing import Dict, Any
from model import MyModel
from loguru import logger
from metrics import MODEL_PREDICTION_PROBABILITY, PREDICTIONS_TOTAL, PREDICTION_DURATION
from errors import ModelUninitialized

with open('config.yaml', 'r') as file:
    CONFIG = yaml.safe_load(file)


class ModelService:    
    _instance = None
    model_wrapper: MyModel = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def init(cls):
        if cls.model_wrapper is None:
            cls.model_wrapper = MyModel()
            
            logger.info('Инициализация модели.')
            cls.model_wrapper.init_model()
            logger.info('Модель инициализирована успешно!')

    @classmethod
    def get_model(cls):
        return cls.model_wrapper.model

    @classmethod
    def is_initialized(cls):
        return cls.model_wrapper is not None and cls.model_wrapper.model is not None
    
    @classmethod
    def predict(
        cls, 
        request_data: Dict[str, Any]
    ) -> int:
        if not cls.is_initialized():
            raise ModelUninitialized("Модель не инициализирована")
        try:
            start_time = time.time()
            prediction, probability = cls.model_wrapper.predict(request_data)
            duration = time.time() - start_time

            is_violation = bool(prediction)
            result_label = "violation" if is_violation else "ok"
            
            PREDICTION_DURATION.observe(duration)
            PREDICTIONS_TOTAL.labels(result=result_label).inc()
            MODEL_PREDICTION_PROBABILITY.labels(prediction_type="inference").set(probability)
                    
            return is_violation, probability
        except Exception as e:
            logger.error(f"Ошибка при предсказании: {e}")
            raise
    
