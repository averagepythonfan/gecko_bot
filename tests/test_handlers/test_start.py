import os
import sys

# sys.path.extend([os.getcwd(),
#                  os.getcwd()+'/bot',
#                  os.getcwd()+'/fastapi',
#                  os.getcwd()[:-19],
#                  os.getcwd()[:-19]+'/bot',
#                  os.getcwd()[:-19]+'/fastapi'])

from unittest.mock import AsyncMock
import pytest
import datetime
from bot.handlers.handlers import help_command
from bot.handlers.help_command import help_str
from aiogram.types import Message, User, Chat


async def test_start_handler():
    message = Message(
        message_id=42,
        date=datetime.datetime.now(),
        text="test",
        chat=Chat(id=42, type="private"),
        from_user=User(id=52243, is_bot=False, first_name='eugene',username='Jabba')
    )
    await help_command(message)
