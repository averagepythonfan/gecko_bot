__all__ = [
    'unit_of_work'
]

from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from config import DATABASE, MONGONET
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult


class MongoRepo:

    def __init__(self, collection: str, ip: str = MONGONET, port: int = 27017, database: str = DATABASE) -> None:
        self.client = AsyncIOMotorClient(ip, port)
        self.database = self.client[database]
        self.collection = self.database[collection]
        self.object_id = None

    async def create(self, query: dict) -> bool:
        res: InsertOneResult = await self.collection.insert_one(query)
        self.object_id = res.inserted_id
        return res.acknowledged

    async def read(self, query: dict = None, projection: dict = {}) -> dict | None:
        _query = query if self.object_id is None else {'_id': self.object_id}
        res = await self.collection.find_one(_query, projection)
        if res:
            self.object_id = res['_id']
            return res

    async def update(self, query: dict, filter_: dict = None) -> bool:
        _filter = filter_ if self.object_id is None else {'_id': self.object_id}
        res: UpdateResult = await self.collection.update_one(
            _filter,
            query
        )
        return res.acknowledged

    async def delete(self, query: dict = None) -> bool:
        _query = query if self.object_id is None else {'_id': self.object_id}
        res: DeleteResult = await self.collection.delete_one(_query)
        return res.acknowledged

    async def find_id(self, query: dict, projection: dict = {'_id': 1}) -> str | None:
        return await self.collection.find_one(query, projection)


@asynccontextmanager
async def unit_of_work(collection: str):
    m = MongoRepo(collection=collection)
    async with await m.client.start_session() as s:
        async with s.start_transaction():
            yield m
