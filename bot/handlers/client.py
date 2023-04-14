import aiohttp
from config import FASTAPI


class Client:

    @staticmethod
    async def get(entity: str,
                  path: str,
                  headers: dict = {'accept': 'application/json',},
                  params: dict = {}) -> dict:
        '''GET method: no body allowed.
        Return a json.'''

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'http://{FASTAPI}:80{entity}{path}',
                params=params,
                headers=headers
            ) as resp:
                response = await resp.json()
        return response
    
    @staticmethod
    async def put(entity: str,
                  path: str,
                  headers: dict = {'accept': 'application/json',
                                   'Content-Type': 'application/json',},
                  json_data: dict = {}) -> dict:
        '''PUT method: only for users'''

        async with aiohttp.ClientSession() as session:
            async with session.put(
                f'http://{FASTAPI}:80{entity}{path}',
                headers=headers,
                json=json_data
            ) as resp:
                response = await resp.json()
        return response
    
    @staticmethod
    async def post(entity: str,
                   path: str,
                   headers: dict = {'accept': 'application/json',
                                    'Content-Type': 'application/json',},
                   json_data: dict = {}) -> dict:
        '''POST mothod: all types'''

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'http://{FASTAPI}:80{entity}{path}',
                headers=headers,
                json=json_data
            ) as resp:
                response = await resp.json()
        return response
    
    @staticmethod
    async def delete(entity: str,
                     path: str,
                     headers: dict = {'accept': 'application/json',},
                     json_data: dict = {}) -> dict:
        '''DELETE method: only for users'''

        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f'http://{FASTAPI}:80{entity}{path}',
                headers=headers,
                json=json_data
            ) as resp:
                response = await resp.json()
        return response
