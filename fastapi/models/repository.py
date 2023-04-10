import aiohttp
from mongodb import users, pairs, other

__all__ = [
    'Other',
    'Users',
    'Pairs'
]


class Users:
    '''CRUD pattern for users.'''

    @staticmethod
    async def create_user(user_id: int):
        pass

    @staticmethod
    async def get_user(user_id: int):
        res = await users.find_one({'user_id': user_id})
        return res
    
    @staticmethod
    async def set_n_pairs(user_id: int, n_pairs: int):
        pass

    @staticmethod
    async def delete_user(user_id: int):
        pass


class Other:
    '''Class for coins and currencies aggregation.
    It has two static methods: for update and validation pair.
    '''

    @staticmethod
    async def update():
        '''Update supported vs_currencies and coins list.
        
        Returns an inserted id after success request,
        otherwise returns None.'''

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
    async def pair_existence(pair: list) -> dict | str:
        '''Check if pair exist. Returns boolean values, or index of error:

        :return: 432 - Wrong vs_currency.
        :return: 433 - Wrong coin.
        :return: 200 - Everything is correct.
        '''

        data = {'coin': False, 'vs_currency': False}

        vs_currency = await other.find_one(
            {'name': 'supported_vs_currencies',
             'data': {
                '$in': [pair[1]]
                }
            }
        )
        if vs_currency:
            data['vs_currency'] = True
        else:
            return 432

        coin = await other.find_one(
            {'name': 'coins_list',
            'data': {
                '$elemMatch':
                    {'id': pair[0]}
                }
            }
        )
        if coin:
            data['coin'] = True
        else:
            return 433

        return 200

class Pairs:
    '''CRUD for pairs'''

    @staticmethod
    async def add_pair(pair: list):
        result = await Other.pair_existence(pair=pair)
        if result != 200:
            return result
        ...
    
    @staticmethod
    async def get_pair(pair: str, days: int):
        pass

    @staticmethod
    async def delete_pair(pair: list):
        pass