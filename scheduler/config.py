import os

MONGO = os.getenv('MONGO')
MLFLOW_CLIENT = os.getenv('MLFLOW_CLIENT')
MLFLOW_SERVER = os.getenv('MLFLOW_SERVER')
ADMIN: int = int(os.getenv('ADMIN'))
TOKEN: str = os.getenv('TOKEN')
