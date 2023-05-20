import os


MONGONET: str = '172.19.0.2' #os.getenv('MONGONET')
TOKEN: str = os.getenv('TOKEN')
REDIS: str = os.getenv('REDIS')
MLFLOW_CLIENT: str = os.getenv('MLFLOW_CLIENT')
MLFLOW_SERVER: str = os.getenv('MLFLOW_SERVER')
DATABASE: str = 'test_db' #os.getenv('DATABASE')
