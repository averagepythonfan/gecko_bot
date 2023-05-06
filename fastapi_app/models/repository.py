__all__ = [
    'Other',
    'Users',
    'Pairs'
]


import aiohttp
import time
import os
import pandas as pd
import logging
import seaborn as sns
import matplotlib.pyplot as plt
from .misc import redis_aio, validate_user_data, send_pic, make_pic
from mongodb import users, pairs, other
from .models import Pair, User
from pymongo import ReturnDocument, DESCENDING
from pymongo.results import DeleteResult, InsertOneResult
from config import TOKEN


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

sns.set_theme(style="darkgrid")

class Other:
    '''Class for coins and currencies aggregation.
    It has two static methods: for update and validation pair.'''

    @staticmethod
    async def update():
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
        else:
            return 433

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
        result = await Other.pair_in_database(coin_id=coin_id, vs_currency=vs_currency, day=day)
        if result == 433:
            return result
        else:
            return result['data']['prices']

    @staticmethod
    async def get_pic(user_id: int, coin_id: str, vs_currency: str, day: int = 7):
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

                    url = f'https://api.telegram.org/bot{TOKEN}/sendPhoto?chat_id={user_id}'

                    response = await send_pic(
                        file_name=file_name,
                        url=url
                    )
                    os.remove(file_name)

                    async with redis_aio() as redis:
                        await redis.set(
                            name=f'{pair} {day}',
                            value=response['result']['photo'][-1]['file_id'],
                            ex=600
                        )
                    logger.info(f'pair: {coin_id}-{vs_currency}, resp {response}')
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
        _users = []
        cur = users.find().sort('user_id', DESCENDING)
        docs = await cur.to_list(None)
        for el in docs:
            _users.append(validate_user_data(el))
        return _users

    @staticmethod
    async def get_user(user_id: int):
        res = await users.find_one({'user_id': user_id})
        if res:
            return validate_user_data(res)

    @staticmethod
    async def set_n_pairs(user_id: int, n_pairs: int = 3):
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
