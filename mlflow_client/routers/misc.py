import mlflow
import time
import pandas as pd
from mlflow import MlflowClient
from config import MLFLOW
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics


def get_client() -> MlflowClient:
    client = MlflowClient(tracking_uri=f'http://{MLFLOW}:5000')
    yield client
    del client

def single_run(df: str, experiment_id: str) -> dict:
    '''Create a single run. Return a dict with response.'''
    read = pd.read_json(df)
    read.ds = pd.to_datetime(read.ds//1000, unit='s')
    time_now = int(time.time()) // 1000
    try:
        m = Prophet()
        mlflow.start_run(
            experiment_id=experiment_id,
            run_name=f'prophet_run_{time_now}',
            tags={"model": "prophet", "priority": "P1"},
            description=f'Model create run at {time_now}'
        )
        m.fit(read)

        model_params = {
                name: value for name, value in vars(m).items() if np.isscalar(value)
        }
        mlflow.log_params(model_params)

        cv_results = cross_validation(
                m, initial='1800 hours', period='60 hours', horizon='120 hours'
            )
            
        cv_metrics = ["mse", "rmse", "mape"]
        metrics_results = performance_metrics(cv_results, metrics=cv_metrics)
        average_metrics = metrics_results.loc[:, cv_metrics].mean(axis=0).to_dict()
        mlflow.log_metrics(average_metrics)
        model_info = mlflow.prophet.log_model(m, "prophet-model")
        mlflow.end_run()
        return {
            'code': 200,
            'detail': {
                'message': 'successful run',
                'model_uri': model_info.model_uri
            }
        }
    except Exception as e:
        return f'Exception {e}'
