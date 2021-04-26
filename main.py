import asyncio
import logging

from client import client
from bot.bot import create_bot

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)

    bot = create_bot()

    asyncio.get_event_loop().run_until_complete(client.create_client(bot))
