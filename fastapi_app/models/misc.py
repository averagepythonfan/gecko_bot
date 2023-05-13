from contextlib import asynccontextmanager
import time
import aiohttp
import aioredis
from pydantic import BaseModel
from typing import List
import pandas as pd
from pandas.core.frame import DataFrame
import matplotlib.pyplot as plt
import seaborn as sns
from config import REDIS, TOKEN


sns.set_theme(style="darkgrid")


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


def make_forecast_pic(
        prices: list,
        forecast: str,
        user_id: int,
        pair: str,
        day_before: int = 12
    ) -> str:
    '''Makes a pic with forecast data.
    
    Return a file name (format: '{user_id}-{int(time.time())}.jpeg').'''

    df = pd.DataFrame(prices, columns=['ds', 'y'])
    df.ds = pd.to_datetime(df.ds // 1000, unit='s')

    forecast = pd.read_json(forecast)
    forecast.ds = pd.to_datetime(forecast.ds // 1000, unit='s')

    treshold = -(24 * day_before)
    target_list = ['yhat_upper', 'yhat_lower', 'yhat']
    
    plt.figure(figsize=(17,8), dpi=80)
    plot = sns.lineplot(data=df, x=df.ds[treshold:], y=df.y[treshold:], label='data')
    for target in target_list:
        diff = df.y.iloc[-1] - forecast[target].iloc[0]
        sns.lineplot(data=forecast, x=forecast.ds, y=forecast[target]+diff, label=target)
    plot.set(xlabel=f'Last {-treshold//24} days', ylabel='Closing Price')
    plot.set_title(pair)
    plot.legend(loc=0)

    fig = plot.get_figure()
    file_name = f'{user_id}-{int(time.time())}.jpeg'
    fig.savefig(file_name)

    plt.clf()

    return file_name


@asynccontextmanager
async def redis_aio():
    '''aioredis context manager.'''

    redis = aioredis.from_url(f'redis://{REDIS}')
    yield redis
    await redis.close()
