import os
import numpy as np
import yaml

from typing import Dict, Any
from model import MyModel
from loguru import logger


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
            
            if not cls.model_wrapper.model_exists():
                logger.info("Модель еще не обучена. Производится обучение...")
                cls.model_wrapper.fit()
                cls.model_wrapper.save_model()
                logger.info("Модель обучена и сохранена успешно!")
            else:
                logger.info("Загрузка модели из файла...")
                cls.model_wrapper.load_model()
                logger.info("Модель загружена!")

    @classmethod
    def is_initialized(cls):
        return cls.model_wrapper is not None and cls.model_wrapper.model is not None

    @classmethod
    def extract_features(
        cls, 
        request_data: Dict[str, Any]
    ) -> np.ndarray:

        if not cls.is_initialized():
            raise ValueError("Модель не инициализирована")

        logger.info(f"Обработка признаков для: item_id={request_data['item_id']} и seller_id={request_data['seller_id']}")
        
        model_feats = cls.model_wrapper.get_feats()

        normalization_const_postfix = '_normalize'

        feature_vector_prep = []
        for feature in model_feats:

            if feature.endswith('_len'):
                feature_name = feature.split('_len')[0]
                request_data[feature] = len(request_data[feature_name])
            
            feature_value = request_data[feature]

            if CONFIG['model'].get(feature + normalization_const_postfix, None) is not None:
                normalized_const = CONFIG['model'][feature + normalization_const_postfix]
                feature_vector_prep.append(feature_value / normalized_const)
                continue

            if feature == 'is_verified_seller':
                feature_vector_prep.append(1.0 if request_data['is_verified_seller'] else 0.0)
                continue

            feature_vector_prep.append(feature_value)

        feature_vector_prep = np.array([feature_vector_prep])
                
        logger.info(f"Подготовленный вектор признаков: {feature_vector_prep}")
        return feature_vector_prep
    
    @classmethod
    def predict(
        cls, 
        features: np.ndarray
    ) -> int:
        if not cls.is_initialized():
            raise ValueError("Модель не инициализирована")
        try:
            prediction  = cls.model_wrapper.predict(features)
            probability = cls.model_wrapper.predict_proba(features)
            
            is_violation = bool(prediction)
                    
            return is_violation, probability
        except Exception as e:
            logger.error(f"Ошибка при предсказании: {e}")
            raise
    
