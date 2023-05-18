import os


MONGONET: str = os.getenv('MONGONET')
TOKEN: str = os.getenv('TOKEN')
REDIS: str = os.getenv('REDIS')
MLFLOW_CLIENT: str = os.getenv('MLFLOW_CLIENT')
MLFLOW_SERVER: str = os.getenv('MLFLOW_SERVER')
EXPERIMENT: str = 'main_experiment'
DATABASE: str = 'main_database'
