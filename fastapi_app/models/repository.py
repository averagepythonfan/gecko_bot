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
from pandas.core.frame import DataFrame
from .misc import redis_aio, validate_user_data, send_pic, make_pic, make_forecast_pic
from mongodb import users, pairs, other
from .models import Pair, User
from pymongo import ReturnDocument, DESCENDING
from pymongo.results import DeleteResult, InsertOneResult
from config import EXPERIMENT, TOKEN, MLFLOW_CLIENT, MLFLOW_SERVER


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Other:
    '''Class for coins and currencies aggregation.
    It has two static methods: for update and validation pair.'''

    @staticmethod
    async def update():
        '''Update a pair data from GeckoCoin.
        Uses from a checking if pair exist.'''

        headers = {
            'accept': 'application/json',
        }

        data = {
            'supported_vs_currencies': 'https://api.coingecko.com/api/v3/simple/supported_vs_currencies',
            'coins_list': 'https://api.coingecko.com/api/v3/coins/list'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                for title, url in data.items():
                    async with session.get(url, headers=headers) as resp:
                        response = {'name': title, 'data': await resp.json()}
                        result = await other.insert_one(response)
            
            return result.inserted_id

        except Exception:
            return None
    
    @staticmethod
    async def pair_existence(pair: Pair) -> dict:
        '''Check if pair exist. Returns status code.

        :return: 432 - Wrong vs_currency.
        :return: 433 - Wrong coin.
        :return: 200 - Everything is correct.'''

        vs_currency = await other.find_one(
            {'name': 'supported_vs_currencies',
             'data': {
                '$in': [pair.vs_currency]
                }
            }
        )
        if vs_currency is None:
            return {'code': 432, 'detail': 'vs_currency is incorrect'}

        coin = await other.find_one(
            {'name': 'coins_list',
            'data': {
                '$elemMatch':
                    {'id': pair.coin_id}
                }
            }
        )
        if coin is None:
            return {'code': 433, 'detail': 'coin is incorrect'}
        
        return {'code': 200, 'detail': 'pair is valid'}

    @staticmethod
    async def pair_in_database(coin_id: str, vs_currency: str, day: int = 7):
        '''Return pair data if it exists.
        Otherwise return 433 response: Pair does not exist.'''

        time_slice = -(day * 24)
        res = await pairs.find_one(
            {'pair_name': f'{coin_id}-{vs_currency}'},
                {
                    'data': {
                        'prices': {'$slice': time_slice},
                        'market_caps': {'$slice': 0},
                        'total_volumes': {'$slice': 0}
                            }
                }
            )
        if res:
            return res

    
    @staticmethod
    async def checker(user_id: int, coin_id: str, vs_currency: str, day: int) -> dict | None:
        '''Check if user exist, pair exist in user's list and database.
        
        If all is "True" return pair data.
        Otherwise, returns None.'''

        default = {
            'user_exist': False,
            'pair_in_db': False,
            'pair_in_users_list': False,
        }
        pair = f'{coin_id}-{vs_currency}'
        user = await users.find_one({'user_id': user_id})
        if user:
            if pair in user['pairs']:
                default['pair_in_users_list'] = True
                pair_in_db = await Other.pair_in_database(
                    coin_id=coin_id,
                    vs_currency=vs_currency,
                    day=day
                )
                if pair_in_db:
                    default['pair_in_db'] = True
            default['user_exist'] = True
        
        if all(default.values()):
            return pair_in_db


class Pairs:
    '''CRUD for pairs'''

    @staticmethod
    async def add_pair(pair: Pair):
        result = await Other.pair_existence(pair=pair)
        if result != 200:
            return result
        else:
            headers = {
                'accept': 'application/json',
            }

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
                    headers=headers) as resp:
                        pair_data = await resp.json()
            
            res: InsertOneResult = await pairs.insert_one({
                'pair_name': f'{pair.coin_id}-{pair.vs_currency}',
                'data': pair_data
            })

            return res.inserted_id

    @staticmethod
    async def get_pair(coin_id: str, vs_currency: str, day: int = 7):
        '''Extract data from database.
        
        If it exists, return a JSON data,
        otherwise return 433 response: Pair does not exist.'''

        result = await Other.pair_in_database(coin_id=coin_id, vs_currency=vs_currency, day=day)
        if result == 433:
            return result
        else:
            return result['data']['prices']

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

        user = await users.find_one({'user_id': user_id})
        if user:
            pair = f'{coin_id}-{vs_currency}'
            if pair in user['pairs']:
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
                
                check_pair = await Other.pair_in_database(
                    coin_id=coin_id,
                    vs_currency=vs_currency,
                    day=day
                )
                if check_pair != 433:
                    prices = check_pair['data']['prices']

                    file_name = make_pic(
                        prices=prices,
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

                    return {'code': 200, 'detail': response }
                else:
                    return {'code': 433, 'detail': 'pair incorrect'}
            else:
                return {'code': 437, 'detail': 'pair not found in user pair list'}
        else:
            return {'code': 434, 'detail': 'user not found'}


    @staticmethod
    async def delete_pair(pair: Pair):
        pass


class Users:
    '''CRUD pattern for users.'''

    @staticmethod
    async def create_user(user: User):
        '''Creates a new user, if it does not exist.
        
        :return: True - user successfully created
        :return: None - user alredy exists.'''

        res = await users.find_one({'user_id': user.user_id})
        if res:
            return None
        else:
            user_data = {
                'user_id': user.user_id,
                'user_name': user.user_name,
                'n_pairs': user.n_pairs,
                'pairs': []
            }
            result: InsertOneResult = await users.insert_one(user_data)
            return result.acknowledged

    @staticmethod
    async def get_all_users():
        '''Return all users data'''

        _users = []
        cur = users.find().sort('user_id', DESCENDING)
        docs = await cur.to_list(None)
        for el in docs:
            _users.append(validate_user_data(el))
        return _users

    @staticmethod
    async def get_user(user_id: int):
        '''Get user data by user_id'''

        res = await users.find_one({'user_id': user_id})
        if res:
            return validate_user_data(res)

    @staticmethod
    async def set_n_pairs(user_id: int, n_pairs: int = 3):
        '''Set count of available pair fot selected user (user_id)'''

        res = await users.find_one_and_update(
            {'user_id': user_id},
            {'$set': {'n_pairs': n_pairs}},
            return_document=ReturnDocument.AFTER
        )
        if res:
            return validate_user_data(res)

    @staticmethod
    async def add_pair(user_id: int, pair: Pair):
        data = {
            'code': 200,
            'detail': 'pair successfully added'
        }

        check_user = await users.find_one({'user_id': user_id})
        check_pair = await Other.pair_existence(pair=pair)

        if (check_user and check_pair['code'] == 200):
            user_validated = validate_user_data(check_user)
            if user_validated['n_pairs'] > len(user_validated['pairs']):
                res = await users.find_one_and_update(
                    {'user_id': user_id},
                    {'$push': {'pairs': f'{pair.coin_id}-{pair.vs_currency}'}},
                    return_document=ReturnDocument.AFTER
                )
                user_updated = validate_user_data(res)
                data['detail'] = {
                    'message': 'user and pair successfully validated and added',           
                    'data': user_updated,
                    'n_user_pairs': len(user_updated['pairs']),
                    'n_pairs_left': user_updated['n_pairs'] - len(user_updated['pairs'])
                }
            else:
                data['code'] = 439
                data['detail'] = 'Pair limit is over'
        elif check_pair != 200:
            data['code'] = check_pair['code']
            data['detail'] = check_pair['detail']
        elif check_user is None:
            data['code'] = 435
            data['detail'] = 'user not found'
        return data

    @staticmethod
    async def delete_users_pair(user_id: int, pair: str):
        data = {
            'code': 200,
            'detail': 'pair successfully deleted'
        }

        res = await users.find_one_and_update(
            {'user_id': user_id},
            {'$pull': {'pairs': pair}}
        )
        if res is None:
            data['code'] = 437
            data['detail'] = 'pair not found'
        
        return data

    @staticmethod
    async def delete_user(user_id: int):
        res: DeleteResult = await users.delete_one({'user_id': user_id})
        return res.raw_result


class Models:

    main_experiment: str = EXPERIMENT

    @classmethod
    async def get_model_uri(cls, model: str = 'prophet-model') -> dict | None:
        '''Class method return a dict with model_uri and last_day.
        
        If any exception raise then return None.
        Format:
        {
            "model_uri": "runs:/844793cfeeb44e01b9f27b8ca15b015e/prophet-model",
            "last_day": "2023-04-12 20:00:30"
        }'''

        async with aiohttp.ClientSession() as session:

            url_get = f'http://{MLFLOW_SERVER}:5000/api/2.0/mlflow/experiments/get-by-name'
            params = {'experiment_name': cls.main_experiment}

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
    
    @staticmethod
    async def send_forecast_pic(user_id: int, pair: Pair, forecast: str, day_before: int = 12):
        '''Makes a picture with forecast for user.
        
        Send it by Telegram Bot API.'''

        res = await Other.checker(
            user_id=user_id,
            coin_id=pair.coin_id,
            vs_currency=pair.vs_currency,
            day=day_before
        )

        if res:
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
                prices=res['data']['prices'],
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