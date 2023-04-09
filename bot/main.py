import logging
import asyncio
from aiogram import Bot, Dispatcher
from handlers import register_message_handlers
from config import TOKEN


async def main():
    '''Main command which set logging and polling'''

    logging.basicConfig(level=logging.DEBUG)

    dp = Dispatcher()
    bot = Bot(token=TOKEN)

    register_message_handlers(dp)

    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print('Goodbye!')