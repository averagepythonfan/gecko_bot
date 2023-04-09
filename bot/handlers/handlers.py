from aiogram import Router, types
from aiogram.filters import Command


__all__ = [
    'register_message_handlers'
]


async def help_command(message: types.Message):
    '''Send help information to user'''

    await message.reply('''
        THIS IS A HELP COMMAND !
    ''')


def register_message_handlers(router: Router):
    router.message.register(help_command, Command(commands=['help']))
