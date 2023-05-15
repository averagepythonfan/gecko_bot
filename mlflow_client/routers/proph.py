import requests
import mlflow
import pandas as pd
from mlflow import MlflowClient
from fastapi import APIRouter, Depends, HTTPException
from config import MLFLOW, FASTAPI
from .misc import get_client, single_run
from mlflow.exceptions import RestException


# settings
router = APIRouter(
    prefix='/prophet',
    tags=['Prophet']
)
mlflow.set_tracking_uri(f'http://{MLFLOW}:5000')


@router.post('/do_run')
def create_prophet_run(coin_id: str, vs_currency: str, client: MlflowClient = Depends(get_client)):
    '''Create a one run of Prophet Model.

    Firstly, it find a existing experiment by name.
    If experiment does not exist, create a new one.
    Then create a run, save metadata and fitted model.
    Return
    
    Parameters
    ----------
    
    coin_id:
        coin id, must be string.
        for example: bitcoin, ethereum, etc.
    vs_currency:
        mast be string, examples: usd, rub, eth
    client:
        mlflow client to work with mlflow API.
        
    Return a dict with format:
        :return:code: 200 - successful run
        :return:code: 433 - failed run'''

    EXPERIMENT = f'{coin_id}-{vs_currency}'

    headers = {
    'accept': 'application/json',
    }

    params = {
        'coin_id': coin_id,
        'vs_currency': vs_currency,
        'day': '89',
    }

    response = requests.get(f'http://{FASTAPI}/pair/get_pair', params=params, headers=headers)

    prices = response.json()['prices']
    df = pd.DataFrame(prices, columns=['ds', 'y'])
    df.ds = df.ds // 1000
    df.ds = pd.to_datetime(df.ds, unit='s')

    exp = client.get_experiment_by_name(EXPERIMENT)
    if exp:
        res = single_run(
            df=df,
            experiment_id=exp.experiment_id
        )
    else:
        exp_id = mlflow.create_experiment(EXPERIMENT)
        res = single_run(
            df=df,
            experiment_id=exp_id
        )
    if isinstance(res, str):
        raise HTTPException(
            status_code=443,
            detail={
                'message': 'failed run',
                'data': res
            }
        )
    else:
        return res


@router.post('/predict')
def predict_prophet(day: int, model_uri: str, last_data: str):
    '''Forecast for {day}
    
    Parameters
    ----------
    
    day:
        integer value, recomended 1-7 days
    model:
        format: "runs:/095f1115756e4cb2af968f25664fd569/prophet-model"
    last_data:
        format: "2023-04-12 20:00:30"

    Rerurn a JSON
        :return:code: 200 - forecast data
        :return:code: 444 - value error'''
    try:
        loaded_model = mlflow.pyfunc.load_model(model_uri)

        test_dates = pd.date_range(start=last_data, periods=24*day, freq="H")
        test_df = pd.Series(data=test_dates.values, name="ds").to_frame()

        preds = loaded_model.predict(test_df)
        return {
            'code': 200,
            'predictions': preds.to_json()
        }
    except (RestException, OSError) as e:
        raise HTTPException(
            status_code=444,
            detail={
                'message': f'{model_uri} not found',
                'data': f'{e}'
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=445,
            detail={
                'message': f'{e}'
            }
        )
