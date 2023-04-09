__all__ = [
    'users',
    'pairs',
    'other'
]

from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGONET

# init client, database and collections for mongodb
URL = f'mongodb://{MONGONET}:27017'
client = AsyncIOMotorClient(URL)
db = client.main_database

users = db.users
pairs = db.pairs
other = db.other
