import aiohttp
import time
from .misc import validate_user_data
from mongodb import users, pairs, other
from .models import Pair, User, UserResponse
from pymongo import ReturnDocument, DESCENDING
from pymongo.results import DeleteResult, InsertOneResult

__all__ = [
    'Other',
    'Users',
    'Pairs'
]


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
    async def pair_existence(pair: Pair) -> int:
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
            return 432

        coin = await other.find_one(
            {'name': 'coins_list',
            'data': {
                '$elemMatch':
                    {'id': pair.coin_id}
                }
            }
        )
        if coin is None:
            return 433
        
        return 200

    @staticmethod
    async def pair_in_database(coin_id: str, vs_currency: str):
        res = await pairs.find_one({'pair_name': f'{coin_id}-{vs_currency}'})
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
    async def get_pair(coin_id: str, vs_currency: str, days: int = 0):
        result = await Other.pair_in_database(coin_id=coin_id, vs_currency=vs_currency)
        if result == 433:
            return result
        else:
            return result['data']['prices']

    @staticmethod
    async def delete_pair(pair: list):
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
            return result.inserted_id

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
    async def set_n_pairs(user: User):
        res = await users.find_one_and_update(
            {'user_id': user.user_id},
            {'$set': {'n_pairs': user.n_pairs}},
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

        res = await users.find_one({'user_id': user_id})
        res_pair = await Other.pair_existence(pair=pair)

        if (res and res_pair == 200):
            res_update =  await users.find_one_and_update({
                {'user_id': user_id},
                {'$push': {'pairs': f'{pair.coin_id}-{pair.vs_currency}'}}
            })
        elif res_pair != 200:
            data['code'] = res_pair
            data['detail'] = 'pair does not exist'
        elif res is None:
            data['code'] = 435
            data['detail'] = 'user not found'
        return data

    @staticmethod
    async def delete_users_pair(user_id: int, pair: str):
        data = {
            'code': 200,
            'detail': 'pair successfully added'
        }

        res = await users.find_one_and_update({'user_id': user_id}, {'$pull': {'pairs': pair}})
        if res is None:
            data['code'] = 437
            data['detail'] = 'pair not found'
        
        return data

    @staticmethod
    async def delete_user(user_id: int):
        res: DeleteResult = await users.delete_one({'user_id': user_id})
        return res.raw_result
    