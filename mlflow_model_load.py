import mlflow
import yaml

from mlflow.sklearn import log_model
from services.model_service import ModelService

ModelService.init()

with open('config.yaml', 'r') as file:
    CONFIG = yaml.safe_load(file)

mlflow.set_tracking_uri(CONFIG["mlflow"]["tracking_uri"])
mlflow.set_experiment(CONFIG["mlflow"]["experiment_name"])

with mlflow.start_run():
    model = ModelService.get_model()

    log_model(model, "my_model", registered_model_name=CONFIG["mlflow"]["registry_model_name"])