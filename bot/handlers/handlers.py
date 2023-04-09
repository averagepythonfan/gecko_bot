import aiohttp
from aiogram import Router, types
from aiogram.filters import Command
from config import GECKONET


__all__ = [
    'register_message_handlers'
]


async def help_command(message: types.Message):
    '''Send help information to user'''

    await message.reply('''
        THIS IS A HELP COMMAND !
    ''')


async def healthcheck_fastapi_command(message: types.Message):
    ''' '''
    async with aiohttp.ClientSession() as session:
        async with session.get(f'http://{GECKONET}:80/healthcheck') as resp:
            text = await resp.text()
    await message.reply(text=text)



def register_message_handlers(router: Router):
    router.message.register(help_command, Command(commands=['help']))
    router.message.register(healthcheck_fastapi_command, Command(commands=['fastapi']))