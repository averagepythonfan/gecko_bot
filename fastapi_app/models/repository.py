__all__ = [
    'Other',
    'Users',
    'Pairs',
    'Models'
]


import aiohttp
import time
import os
import logging
from .misc import redis_aio, send_pic, make_pic, make_forecast_pic
from mongodb import unit_of_work
from .models import Pair, User
from pymongo import DESCENDING
from config import TOKEN, MLFLOW_CLIENT, MLFLOW_SERVER
from .exc import *


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Other:
    '''Class for coins and currencies aggregation.
    It has two static methods: for update and validation pair.'''

    @staticmethod
    async def update() -> bool | None:
        '''Update a pair data from GeckoCoin like supported_vs_currencies and coins_list.
        Makes two requests to GeckoCoinAPI.
        It needs for check if pair {coin_id}-{vs_currency} exists.'''

        headers = {
            'accept': 'application/json',
        }

        data = {
            'supported_vs_currencies': 'https://api.coingecko.com/api/v3/simple/supported_vs_currencies',
            'coins_list': 'https://api.coingecko.com/api/v3/coins/list'
        }
        
        responses = []

        async with aiohttp.ClientSession() as session:

            for title, url in data.items():
                async with session.get(url, headers=headers) as resp:
                    responses.append(
                        {
                            'name': title,
                            'data': await resp.json()
                        }
                    )

        for el in responses:
            async with unit_of_work('other') as uow:
                resp = await uow.read({'name': el['name']})
                if resp:
                    await uow.update({"$set": {'data': el}})
                else:
                    await uow.create(el)

    
    @staticmethod
    async def _pair_existence(pair: Pair) -> dict:
        '''Check if pair exist. Returns status code.

        :return: 432 - Wrong vs_currency.
        :return: 433 - Wrong coin.
        :return: 200 - Everything is correct.'''

        async with unit_of_work('other') as uow:
            vs_currency = await uow.find_id({
                'name': 'supported_vs_currencies',
                'data': {
                    '$in': [pair.vs_currency]
                }
            })
            coin_id = await uow.find_id({
                'name': 'coins_list',
                'data': {
                    '$elemMatch': {'id': pair.coin_id}
                }
            })

        if vs_currency is None:
            raise VsCurrencyIncorrect()

        if coin_id is None:
            raise CoinIdIncorrect()
        
        return {'code': 200, 'detail': 'pair is valid'}

    @staticmethod
    async def pair_in_database(coin_id: str, vs_currency: str, day: int = 7) -> dict | None:
        '''Return pair data if it exists.
        Otherwise return None'''

        time_slice = -(day * 24)

        async with unit_of_work('pairs') as uow:
            query = {'pair_name': f'{coin_id}-{vs_currency}'}
            projection = {
                'data': {
                    'prices': {'$slice': time_slice},
                    'market_caps': 0,
                    'total_volumes': 0
                }
            }
            return await uow.find_id(query=query, projection=projection)

    
    @staticmethod
    async def checker(user_id: int, coin_id: str, vs_currency: str, day: int) -> dict | None:
        '''Check if user exist, pair exist in user's list and database.
        
        If all is "True" return pair data.
        Otherwise, returns None.'''

        pair = f'{coin_id}-{vs_currency}'

        async with unit_of_work('users') as uow:
            user = await uow.read({'user_id': user_id})

        if user:
            if pair in user['pairs']:
                pair_in_db = await Other.pair_in_database(
                    coin_id=coin_id,
                    vs_currency=vs_currency,
                    day=day
                )
                if pair_in_db:
                    return pair_in_db
                else:
                    raise PairNotInDataBase()
            else:
                raise PairNotInUserList()
        else:
            raise UserNotFound()

class Pairs:
    '''CRUD for pairs'''

    @staticmethod
    async def add_pair(pair: Pair) -> bool | None:
        await Other._pair_existence(pair=pair)

        pair_name = f'{pair.coin_id}-{pair.vs_currency}'

        NOW = int(time.time())
        THEN = NOW - 60 * 60 * 24 * 89

        params = {
            'vs_currency': pair.vs_currency,
            'from': THEN,
            'to': NOW,
        }

        async with aiohttp.ClientSession() as session:

            async with session.get(
                f'https://api.coingecko.com/api/v3/coins/{pair.coin_id}/market_chart/range',
                params=params,
                headers={'accept': 'application/json'}) as resp:
                    data = await resp.json()
        
        async with unit_of_work('pairs') as uow:
            if await uow.read({'pair_name': pair_name}, {'_id': 1}):
                return await uow.update({'$set': {'data': data}})
            else:
                return await uow.create({
                    'pair_name': pair_name,
                    'data': data
                })

    # ONLY FOR MLFLOW CLIENT
    @staticmethod
    async def get_pair(coin_id: str, vs_currency: str, day: int = 7):
        '''Extract data from database.
        
        If it exists, return a JSON data,
        otherwise return None response: Pair does not exist.'''

        result = await Other.pair_in_database(coin_id=coin_id, vs_currency=vs_currency, day=day)
        if result:
            return result['data']['prices']
        else:
            raise PairNotInDataBase()


    @staticmethod
    async def get_pic(user_id: int, coin_id: str, vs_currency: str, day: int = 7):
        '''Send pic to user.
        
        Do a POST HTTP-request to Telegram server.
        If any user makes a request it create a pic with data exchanges
        then cache "file_id" and request for 10 min.
        If cache is empty or key is does not exist,
        it creates a new picture.
        
        :return: 200 - JSON response
        :return: 433 - pair is incorrect
        :return: 434 - user does not exist
        :return: 437 - pair not found in user's list.'''

        pair = f'{coin_id}-{vs_currency}'
        pair_data = await Other.checker(
            user_id=user_id,
            coin_id=coin_id,
            vs_currency=vs_currency,
            day=day)

        # check if exist in cache
        async with redis_aio() as redis:
            value = await redis.get(f'{pair} {day}')
            if value:
                value: bytes
                url = f'https://api.telegram.org/bot{TOKEN}/sendPhoto'
                params = {
                    'chat_id': int(user_id),
                    'photo': value.decode("utf-8")
                }
                resp = await send_pic(url=url, params=params)
                return {'code': 200, 'detail': resp }

        file_name = make_pic(
            prices=pair_data['data']['prices'],
            pair=pair,
            user_id=user_id,
            day=day
        )

        response = await send_pic(
            url=f'https://api.telegram.org/bot{TOKEN}/sendPhoto?chat_id={user_id}',
            file_name=file_name
        )
        os.remove(file_name)

        async with redis_aio() as redis:
            await redis.set(
                name=f'{pair} {day}',
                value=response['result']['photo'][-1]['file_id'],
                ex=600
            )

        return True


    @staticmethod
    async def delete_pair(pair: Pair):
        pass


class Users:
    '''CRUD pattern for users.'''

    @staticmethod
    async def create_user(user: User) -> bool:
        '''Creates a new user, if it does not exist.
        
        :return: True - user successfully created
        :return: None - user alredy exists.'''

        async with unit_of_work('users') as uow:
            if await uow.find_id({'user_id': user.user_id}) is None:
                user_data = {
                    'user_id': user.user_id,
                    'user_name': user.user_name,
                    'n_pairs': user.n_pairs,
                    'pairs': []
                }
                if await uow.create(query=user_data):
                    return True
                else:
                    raise UserCreationError()
            else:
                raise UserAlreadyExist()


    @staticmethod
    async def get_all_users():
        '''Return all users data'''

        async with unit_of_work('users') as uow:
            cur =  uow.collection.find({}, {'_id': 0}).sort('user_id', DESCENDING)
            docs = await cur.to_list(None)
            return docs


    @staticmethod
    async def get_user(user_id: int) -> dict:
        '''Get user data by user_id'''

        async with unit_of_work('users') as uow:
            user = await uow.find_id({'user_id': user_id}, {'_id': 0})
        if user:
            return user
        else:
            raise UserNotFound()


    @staticmethod
    async def set_n_pairs(user_id: int, n_pairs: int = 3) -> bool:
        '''Set count of available pair fot selected user (user_id)'''

        async with unit_of_work('users') as uow:
            res = await uow.update(
                query={'$set': {'n_pairs': n_pairs}},
                filter_={'user_id': user_id}
                )
        if res:
            return res
        else:
            raise UserUpdateError()


    @staticmethod
    async def add_pair(user_id: int, pair: Pair):
        '''Add pair to users list.'''

        await Other._pair_existence(pair=pair)

        async with unit_of_work('users') as uow:
            user = await uow.read({'user_id': user_id})
            if user:
                if user['n_pairs'] > len(user['pairs']):
                    pair_name = f'{pair.coin_id}-{pair.vs_currency}'
                    if await uow.update(
                        {'$push': {'pairs': pair_name}}
                    ):
                        return True
                    else:
                        raise UserUpdateError()
                else:
                    raise PairListIsOver()
            else:
                raise UserNotFound()


    @staticmethod
    async def delete_users_pair(user_id: int, pair: str):
        '''Delete pair from pair list'''

        async with unit_of_work('users') as uow:
            if await uow.update(
                query={'$pull': {'pairs': pair}},
                filter_={'user_id': user_id}
            ):
                return True
            else:
                raise UserUpdateError()


    @staticmethod
    async def delete_user(user_id: int):
        '''Delete user by user_id'''

        async with unit_of_work('users') as uow:
            if await uow.delete({'user_id': user_id}):
                return True
            else:
                raise UserUpdateError()


class Models:

    @staticmethod
    async def create_run_by_pair(coin_id: str, vs_currency: str) -> dict | None:
        '''Send request to mlflow client to do run.'''
        async with aiohttp.ClientSession() as session:
            url = f'http://{MLFLOW_CLIENT}:80/prophet/do_run'
            params = {
                'coin_id': coin_id,
                'vs_currency': vs_currency
            }
            async with session.post(url=url,
                                    params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    raise MlflowClientError('Run failed')

    @staticmethod
    async def get_model_uri(pair: str, model: str = 'prophet-model') -> dict | None:
        '''Class method return a dict with model_uri and last_day.
        
        If any exception raise then return None.
        Format:
        {
            "model_uri": "runs:/844793cfeeb44e01b9f27b8ca15b015e/prophet-model",
            "last_day": "2023-04-12 20:00:30"
        }'''

        async with aiohttp.ClientSession() as session:

            url_get = f'http://{MLFLOW_SERVER}:5000/api/2.0/mlflow/experiments/get-by-name'
            params = {'experiment_name': pair}

            async with session.get(url_get,
                                   params=params) as get_resp:
                if get_resp.status == 200:
                    res = await get_resp.json()
                    exp_id = res['experiment']['experiment_id']
                    url_post = f'http://{MLFLOW_SERVER}:5000/api/2.0/mlflow/runs/search'
                    data = {'experiment_ids': [exp_id]}

                    async with session.post(url_post,
                                            json=data) as post_resp:
                        if post_resp.status == 200:
                            runs = await post_resp.json()
                            run_uuid = runs['runs'][0]['info']['run_uuid']
                            model_uri = f'runs:/{run_uuid}/{model}'
                            last_data = [
                                el['value'] for el in runs['runs'][0]['data']['params'] if el['key'] == 'last_day'
                            ]
                            return {
                                'model_uri' : model_uri,
                                'last_data': last_data.pop()
                            }
                        else:
                            raise ModelURINotFound('Model uri not found')
                else:
                    raise MlflowServerError('REST API error')


    @staticmethod
    async def forecast(day: int, model_uri: str, last_data: str):
        '''Forecast for day through Mlflow Client'''

        logger.info(f'params {day} {model_uri} {last_data}')
        async with aiohttp.ClientSession() as session:

            headers = {
                'accept': 'application/json',
                'content-type': 'application/x-www-form-urlencoded',
            }

            params = {
                'day': day,
                'model_uri': model_uri,
                'last_data': last_data,
            }

            async with session.post(
                f'http://{MLFLOW_CLIENT}/prophet/predict',
                params=params,
                headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    raise MlflowClientError('Predict failed')

    
    @staticmethod
    async def send_forecast_pic(user_id: int, pair: Pair, forecast: str, day_before: int = 12):
        '''Makes a picture with forecast for user.
        
        Send it by Telegram Bot API.'''

        pair_data = await Other.checker(
            user_id=user_id,
            coin_id=pair.coin_id,
            vs_currency=pair.vs_currency,
            day=day_before
        )

        if pair_data:
            async with redis_aio() as redis:
                value = await redis.get(f'{pair.coin_id}-{pair.vs_currency} forecast for {day_before}')
                if value:
                    value: bytes
                    url = f'https://api.telegram.org/bot{TOKEN}/sendPhoto'
                    params = {
                        'chat_id': int(user_id),
                        'photo': value.decode("utf-8")
                    }
                    resp = await send_pic(url=url, params=params)
                    return {'code': 200, 'detail': resp }

            file_name = make_forecast_pic(
                prices=pair_data['data']['prices'],
                forecast=forecast,
                user_id=user_id,
                pair=f"{pair.coin_id}-{pair.vs_currency}",
                day_before=day_before
            )

            response = await send_pic(
                url=f'https://api.telegram.org/bot{TOKEN}/sendPhoto?chat_id={user_id}',
                file_name=file_name
            )
            os.remove(file_name)

            async with redis_aio() as redis:
                await redis.set(
                    name=f'{pair.coin_id}-{pair.vs_currency} forecast for {day_before}',
                    value=response['result']['photo'][-1]['file_id'],
                    ex=600
                )

            return {'code': 200, 'detail': response }
