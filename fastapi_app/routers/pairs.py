from fastapi import APIRouter, HTTPException
from models import Pair, Pairs, Models, Other
from models import (CoinIdIncorrect, VsCurrencyIncorrect,
                    UserNotFound, PairNotInDataBase,
                    PairNotInUserList, MlflowServerError,
                    MlflowClientError, ModelURINotFound)

router = APIRouter(
    prefix='/pair',
    tags=['Pairs']
)


@router.post('/add_pair')
async def add_pair(pair: Pair):
    '''Add pair to database.
    
    :return: 200, pair successfully added,
    :return: 432, vs_currency not valid: {vs_currency},
    :return: 433, coin not valid: {pair.coin_id}'''

    try:
        return {
            'status': f'{await Pairs.add_pair(pair=pair)}',
        }
    except CoinIdIncorrect:
        raise HTTPException(
            status_code=433,
            detail='coin is incorrect'
        )
    except VsCurrencyIncorrect:
        raise HTTPException(
            status_code=432,
            detail='vs currency is incorrect'
        )


@router.get('/send_pic')
async def send_pic(user_id: int, coin_id: str, vs_currency: str, day: int = 7):
    '''Send pic to user by POST request to Telegram Bot API.'''
    
    try:
        res = await Pairs.get_pic(
            user_id=user_id,
            coin_id=coin_id,
            vs_currency=vs_currency,
            day=day
        )
        if res:
            return {
                'status': 'success',
                'detail': f'pic send to {user_id}',
                'data': res
            }
    except PairNotInDataBase:
        raise HTTPException(
            status_code=438,
            detail='pair not in database'
        )
    except PairNotInUserList:
        raise HTTPException(
            status_code=436,
            detail='pair not in users list'
        )
    except UserNotFound:
        raise HTTPException(
            status_code=435,
            detail='user not found'
        )


@router.get('/get_pair')
async def get_pair(coin_id: str, vs_currency: str, day: int):
    try:
        res = await Pairs.get_pair(
            coin_id=coin_id,
            vs_currency=vs_currency,
            day=day
        )
        return {
            'status': 'success',
            'prices': res
        }
    except PairNotInDataBase:
        raise HTTPException(
            status_code=438,
            detail='pair not in database'
        )


@router.post('/forecast')
async def forecast_prophet(day: int, user_id: int, pair: Pair, model: str = 'prophet-model'):
    '''Forecast for {day} by {model_uri}'''
    try:
        await Other.checker(
            user_id=user_id,
            coin_id=pair.coin_id,
            vs_currency=pair.vs_currency,
            day=day
        )
        res = await Models.get_model_uri(
            pair=f'{pair.coin_id}-{pair.vs_currency}',
            model=model
        )
        params = dict({'day': str(day), **res})
        forecast = await Models.forecast(**params)

        pic = await Models.send_forecast_pic(
            user_id=user_id,
            pair=pair,
            forecast=forecast['predictions'],
            day_before=day*3

        )
        return {
            'status': 'success',
            'detail': pic
        }

    except PairNotInDataBase:
        raise HTTPException(
            status_code=438,
            detail='pair not in database'
        )
    except PairNotInUserList:
        raise HTTPException(
            status_code=436,
            detail='pair not in users list'
        )
    except UserNotFound:
        raise HTTPException(
            status_code=435,
            detail='user not found'
        )
    except MlflowServerError as e:
        await Models.create_run_by_pair(
            coin_id=pair.coin_id,
            vs_currency=pair.vs_currency
        )
        raise HTTPException(
            status_code=439,
            detail=f'{e}, your model is preparing'
        )
    except MlflowClientError as e:
        raise HTTPException(
            status_code=440,
            detail=f'{e}'
        )
    except ModelURINotFound:
        await Models.create_run_by_pair(
            coin_id=pair.coin_id,
            vs_currency=pair.vs_currency
        )
        raise HTTPException(
            status_code=446,
            detail=f'model {pair.coin_id}-{pair.vs_currency} does not ready'
        )
