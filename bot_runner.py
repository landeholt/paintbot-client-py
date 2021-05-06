import asyncio
from bot.bot import create_bot
from client import client
from client.config import Config
from bot.config import Bot as Bot_config

from dataclasses import dataclass
import orjson as json
import sys


if __name__ == "__main__":
    model_name = sys.argv[1]
    model = __import__(f"models.{model_name}")
    bot_config = Bot_config(name=f"bot-{model_name}", model=model)

    bot = create_bot(bot_config)

    asyncio.get_event_loop().run_until_complete(
        client.create_client(bot, host="ws://localhost:8080", venue="tournament")
    )