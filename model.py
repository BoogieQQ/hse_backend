import pickle
import yaml
import os
import mlflow

import numpy as np

from sklearn.linear_model import LogisticRegression
from loguru import logger
from typing import Dict, Any
from errors import ModelUninitialized


with open('config.yaml', 'r') as file:
    CONFIG = yaml.safe_load(file)


def check_model_init(func):
    def wrapper(self, *args, **kwargs):
        if self.model is None:
            raise ModelUninitialized("Модель не инициализирована. Необходимо вызвать функцию fit!")
        return func(self, *args, **kwargs)
    return wrapper

class MyModel:

    def __init__(self):
        self.model = None

        self.model_path = CONFIG['model']['model_path']
        self.features = CONFIG['model']['features']
        self.use_mlflow = os.getenv("USE_MLFLOW", "false").lower() == "true"

    def init_model(self):
        if self.use_mlflow:
            logger.debug("Включен режим USE_MLFLOW. Загрузка модели из MLflow...")
            self._load_model_mlflow()
            logger.debug("Модель успешно загружена из MLflow!")
        if not self._model_exists():
            logger.debug("Модель еще не обучена. Производится обучение...")
            self._fit()
            self._save_model()
            logger.debug("Модель обучена и сохранена успешно!")
        else:
            logger.debug("Загрузка модели из файла...")
            self._load_model()
            logger.debug("Модель загружена!")
    
    @check_model_init
    def predict(self, request_data: Dict[str, Any]):
        X = self._extract_features(request_data)
        return int(self.model.predict(X)[0]), self.model.predict_proba(X)[:, 1].item()

    def get_feats(self):
        return self.features
    
    def _fit(self):
        """Обучает простую модель на синтетических данных."""
        np.random.seed(42)
        # Признаки: [is_verified_seller, images_qty, description_length, category]
        X = np.random.rand(1000, 4)
        # Целевая переменная: 1 = нарушение, 0 = нет нарушения
        y = (X[:, 0] < 0.3) & (X[:, 1] < 0.2)
        y = y.astype(int)
        
        self.model = LogisticRegression()
        self.model.fit(X, y)
        
        return self.model
    
    def _extract_features(
        self, 
        request_data: Dict[str, Any]
    ) -> np.ndarray:

        logger.debug(f"Обработка признаков для: item_id={request_data['item_id']} и seller_id={request_data['seller_id']}")
        
        model_feats = self.get_feats()

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
                
        logger.debug(f"Подготовленный вектор признаков: {feature_vector_prep}")
        return feature_vector_prep
    
    def _load_model_mlflow(self, version: str = "latest"):
        tracking_uri = CONFIG["mlflow"]["tracking_uri"]

        mlflow.set_tracking_uri(tracking_uri)
            
        model_name = CONFIG["mlflow"]["registry_model_name"]
        model_uri = f"models:/{model_name}/{version}"
        
        try:
            self.model = mlflow.sklearn.load_model(model_uri)
        except Exception as e:
            logger.error(f"Не удалось загрузить модель {model_name} (version: {version}) из MLflow. Ошибка: {e}")
            raise ModelUninitialized("Не удалось загрузить модель из mlflow!")

    def _model_exists(self):
        return os.path.exists(self.model_path)

    def _save_model(self):
        with open(self.model_path, "wb") as f:
            pickle.dump(self.model, f)

    def _load_model(self):
        with open(self.model_path, "rb") as f:
            self.model = pickle.load(f)

