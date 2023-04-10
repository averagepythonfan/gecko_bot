import os
import sys

sys.path.extend([os.getcwd(),
                 os.getcwd()+'/bot',
                 os.getcwd()+'/fastapi',
                 os.getcwd()[:-19],
                 os.getcwd()[:-19]+'/bot',
                 os.getcwd()[:-19]+'/fastapi'])

from unittest.mock import AsyncMock
import pytest
from bot.handlers.handlers import help_command


@pytest.mark.asyncio
async def test_start_handler():
    message = AsyncMock()
    await help_command(message)

    message.reply.assert_called_with('''
        THIS IS A HELP COMMAND !
    ''')