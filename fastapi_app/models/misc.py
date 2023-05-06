from contextlib import asynccontextmanager
import time
import aiohttp
import aioredis
from pydantic import BaseModel
from typing import List
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from config import REDIS


class UserResponse(BaseModel):
    _id: str
    user_id: int
    user_name: str | None
    n_pairs: int
    pairs: List[str | None] | None


def validate_user_data(input_data):
    '''Validate response from mongodb'''

    raw = str(input_data)
    raw = raw.replace('ObjectId(', '').replace(')', '').replace("'", '"')
    valid = UserResponse.parse_raw(raw)
    return valid.dict()


async def send_pic(url: str, file_name: str | None = None, params: dict | None = None) -> dict:
    '''Send pic to user by POST HTTP-request to Telegram API.
    
    Return a JSON with response from Telegram server.

    Parameters
    ----------

    filename:
        format {user_id}-{int(time.time())}.jpeg
    url:
        format https://api.telegram.org/bot{TOKEN}/sendPhoto?chat_id={user_id}'''
    if file_name:
        with open(file_name, 'rb') as img:
            async with aiohttp.ClientSession() as session:
                async with session.post(url=url, data={'photo': img}) as resp:
                    response = await resp.json()
                    return response
    else:
        async with aiohttp.ClientSession() as session:
                async with session.post(url=url, params=params) as resp:
                    response = await resp.json()
                    return response


def make_pic(prices: list, pair: str, user_id: int, day: int):
    '''Make a pic with data prices. Return a file name.

    Parameters
    ----------
    prices:
        list with time and prices
        format [[1680724852129, 28276.702324588], ...]
    pair:
        format 'bitcoin-usd'
    user_id:
        format 2741715718
    day:
        format 7'''

    df = pd.DataFrame(prices, columns=['ds', 'y'])
    df.ds = pd.to_datetime(df.ds // 1000, unit='s')

    plt.figure(figsize=(13,6), dpi=80)
    plot = sns.lineplot(data=df, x=df.ds, y=df.y, label=f'{pair}')
    plot.set(
        title=pair,
        ylabel='value',
        xlabel=f'last {day} days'
    )
    fig = plot.get_figure()
    file_name = f'{user_id}-{int(time.time())}.jpeg'
    fig.savefig(file_name)

    plt.clf()
    return file_name


@asynccontextmanager
async def redis_aio():
    redis = aioredis.from_url(f'redis://{REDIS}')
    yield redis
    await redis.close()

# {
#     'ok': True,
#     'result': {
#         'message_id': 306,
#         'from': {
#             'id': 6136318104,
#             'is_bot': True,
#             'first_name': 'Time Series Forecasting',
#             'username': 'TS_Forecasting_Bot'
#         },
#         'chat': {
#             'id': 875851287,
#             'first_name': 'Евгений',
#             'last_name': 'Исупов',
#             'username': 'forgottenbb',
#             'type': 'private'
#         },
#         'date': 1683367857,
#         'photo': [{
#             'file_id': 'AgACAgIAAxkDAAIBMmRWJ7F_i1Rrznpznyd70_zKpOzXAAL7xTEbCFOxSum3TNf6P9KZAQADAgADcwADLwQ',
#             'file_unique_id': 'AQAD-8UxGwhTsUp4',
#             'file_size': 588,
#             'width': 90,
#             'height': 42
#             }, {
#             'file_id': 'AgACAgIAAxkDAAIBMmRWJ7F_i1Rrznpznyd70_zKpOzXAAL7xTEbCFOxSum3TNf6P9KZAQADAgADbQADLwQ',
#             'file_unique_id': 'AQAD-8UxGwhTsUpy',
#             'file_size': 6048,
#             'width': 320,
#             'height': 148
#             }, {
#             'file_id': 'AgACAgIAAxkDAAIBMmRWJ7F_i1Rrznpznyd70_zKpOzXAAL7xTEbCFOxSum3TNf6P9KZAQADAgADeAADLwQ',
#             'file_unique_id': 'AQAD-8UxGwhTsUp9',
#             'file_size': 23903,
#             'width': 800,
#             'height': 369
#             }, {
#             'file_id': 'AgACAgIAAxkDAAIBMmRWJ7F_i1Rrznpznyd70_zKpOzXAAL7xTEbCFOxSum3TNf6P9KZAQADAgADeQADLwQ',
#             'file_unique_id': 'AQAD-8UxGwhTsUp-',
#             'file_size': 28129,
#             'width': 1040,
#             'height': 480
#             }]
#     }
# }
