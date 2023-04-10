import aiohttp
from aiogram import Router, types
from aiogram.filters import Command
from config import ADMIN, FASTAPI


async def help_command(message: types.Message):
    '''Send help information to user'''

    await message.reply('''
        THIS IS A HELP COMMAND !
    ''')


async def healthcheck_fastapi_command(message: types.Message):
    ''' '''
    if message.from_user.id == int(ADMIN):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://{FASTAPI}:80/healthcheck') as resp:
                text = await resp.text()
        await message.reply(text=text)

async def update_other(message: types.Message):
    '''Update coin and vs_currency data'''
    if message.from_user.id == int(ADMIN):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://{FASTAPI}:80/other') as resp:
                text = await resp.text()
        await message.reply(text=text)


async def check_pair_command(message: types.Message):
    '''Check if pair exist.'''

    pair = message.text[7:].split('-')
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    json_data = {
        'coin_id': pair[0],
        'vs_currency': pair[1],
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f'http://{FASTAPI}/other/exist', headers=headers, json=json_data) as resp:
            text = await resp.json()
    await message.reply(text=text['detail'])


def register_message_handlers(router: Router):
    router.message.register(help_command, Command(commands=['help']))
    router.message.register(healthcheck_fastapi_command, Command(commands=['fastapi']))
    router.message.register(update_other, Command(commands=['update']))
    router.message.register(check_pair_command, Command(commands='check'))
