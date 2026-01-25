import pickle
import yaml
import os

import numpy as np

from sklearn.linear_model import LogisticRegression


with open('config.yaml', 'r') as file:
    CONFIG = yaml.safe_load(file)


def check_model_init(func):
    def wrapper(self, *args, **kwargs):
        if self.model is None:
            raise ValueError("Модель не инициализирована. Необходимо вызвать функцию fit!")
        return func(self, *args, **kwargs)
    return wrapper

class MyModel:

    def __init__(self):
        self.model_path = CONFIG['model']['model_path']
        self.model = None
        self.features = CONFIG['model']['features']

    def fit(self):
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

    @check_model_init
    def predict(self, X: np.ndarray):
        return int(self.model.predict(X)[0])

    @check_model_init
    def predict_proba(self, X: np.ndarray):
        return self.model.predict_proba(X)[:, 1].item()

    def get_feats(self):
        return self.features

    def model_exists(self):
        return os.path.exists(self.model_path)

    def save_model(self):
        with open(self.model_path, "wb") as f:
            pickle.dump(self.model, f)

    def load_model(self):
        with open(self.model_path, "rb") as f:
            self.model = pickle.load(f)

