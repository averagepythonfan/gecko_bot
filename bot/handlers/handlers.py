import aiohttp
from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from config import ADMIN, FASTAPI
from .misc import Entity
from .client import Client
from .help_command import help_str


async def help_command(message: types.Message):
    '''Send help information to user and register him to database.'''

    await Client.post(
        entity=Entity.user.value,
        path='/create',
        json_data={
            'user_id': message.from_user.id,
            'user_name': message.from_user.username,
            'n_pairs': 3,
        }
    )
    await message.reply(text=help_str, parse_mode='HTML')


async def healthcheck_fastapi_command(message: types.Message):
    '''Check FastAPI server is running.'''

    if message.from_user.id == int(ADMIN):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://{FASTAPI}:80/healthcheck') as resp:
                text = await resp.text()
        await message.reply(text=text)


async def update_other(message: types.Message):
    '''Update coin and vs_currency data'''

    if message.from_user.id == int(ADMIN):
        resp = await Client.get(
            entity=Entity.other.value,
            path='/update'

        )
        await message.reply(text=str(resp))


async def set_n_pair_for_user_command(message: types.Message):
    '''Setting n_pair for user: ADMIN only'''

    if message.from_user.id == int(ADMIN):
        text = message.text[5:].split()

        USER_ID = text[0]
        N_PAIRS = text[1]

        resp = await Client.put(
            entity=Entity.user.value,
            path=f'/{USER_ID}/set_n_pairs/{N_PAIRS}'
        )

        await message.reply(text=str(resp))


async def add_pair_command(message: types.Message):
    '''Check if pair exist.'''

    text = message.text[5:].split('-')

    COIN = text[0]
    VS_CURRENCY = text[1]

    resp = await Client.put(
        entity=Entity.user.value,
        path=f'/{message.from_user.id}/add_pair',
        json_data={
            'coin_id': COIN,
            'vs_currency': VS_CURRENCY
        }
    )
    await message.reply(text=str(resp))


async def delete_pair_command(message: types.Message, command: CommandObject):
    '''Delete user's pair'''

    if command.args:
        text = command.args.split('-')

        COIN = text[0]
        VS_CURRENCY = text[1]

        resp = await Client.delete(
            entity=Entity.user.value,
            path=f'/{message.from_user.id}/delete_pair',
            json_data={
                'coin_id': COIN,
                'vs_currency': VS_CURRENCY
            }
        )
        await message.reply(text=str(resp))


async def my_status_command(message: types.Message):
    '''Send user information about him.'''

    resp = await Client.get(
        entity=Entity.user.value,
        path=f'/{message.from_user.id}'
    )

    await message.reply(
        text=f"<b>USER ID</b> : <i>{resp['user_data']['user_id']}</i>\n"
        f"<b>USER NAME</b> : <i>{resp['user_data']['user_name']}</i>\n"
        f"<b>NUMBER OF PAIRS</b> : <i>{resp['user_data']['n_pairs']}</i>\n"
        f"<b>PAIRS</b> : <i>{resp['user_data']['pairs']}</i>",
        parse_mode='HTML')


async def show_exchanges_command(message: types.Message, command: CommandObject):
    '''Send pic with exchanges to user.
    
    Default days = 7'''

    if command.args:
        text = command.args.split()
        pair = text[0].split('-')

        COIN = pair[0]
        VS_CURRENCY = pair[1]
        try:
            DAYS = int(text[1])
        except (IndexError, ValueError):
            DAYS = 7
        finally:
            await Client.get(
                entity=Entity.pair.value,
                path='/send_pic',
                params={
                    'user_id': message.from_user.id,
                    'coin_id': COIN,
                    'vs_currency': VS_CURRENCY,
                    'day': DAYS
                }
            )

async def prophet_forecast(message: types.Message, command: CommandObject):
    '''Forecasting for {days} by prophet model.'''

    if command.args:
        text = command.args.split()
        COIN_ID, VS_CURRENCY = text[0].split('-')
        DAY_FORECAST = text[1]



        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
        }

        params = {
            'day': DAY_FORECAST,
            'user_id': message.from_user.id,
            'model': 'prophet-model',
        }

        json_data = {
            'coin_id': COIN_ID,
            'vs_currency': VS_CURRENCY,
        }


        await Client.post(
            entity=Entity.pair.value,
            path='/forecast',
            headers=headers,
            params=params,
            json_data=json_data
        )


def register_message_handlers(router: Router) -> None:
    router.message.register(help_command, Command(commands=['help', 'start']))
    router.message.register(healthcheck_fastapi_command, Command(commands=['healthcheck']))
    router.message.register(update_other, Command(commands=['update']))
    router.message.register(add_pair_command, Command(commands='add'))
    router.message.register(delete_pair_command, Command(commands=['delete']))
    router.message.register(set_n_pair_for_user_command, Command(commands=['set']))
    router.message.register(my_status_command, Command(commands=['status']))
    router.message.register(show_exchanges_command, Command(commands=['show']))
    router.message.register(prophet_forecast, Command(commands=['prophet']))
