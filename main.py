import asyncio
import logging
import sys

from client import client
from client.config import Message
from bot.bot import create_bot

# from trainer import trainer

from pprint import pformat

FIRST_MESSAGE = True


def print_replace(message):
    sys.stdout.write("\n")
    sys.stdout.write(pformat(message, indent=1, compact=True))
    sys.stdout.flush()


def middleware(message: dict) -> dict:
    global FIRST_MESSAGE
    middleware.hook_type = "test"
    if message["type"] == Message.MapUpdate and FIRST_MESSAGE:
        FIRST_MESSAGE = False
        print_replace(message)

    return message


def main():
    logging.basicConfig(level=logging.INFO)

    bot = create_bot()

    asyncio.get_event_loop().run_until_complete(client.create_client(bot, middlewares=[middleware]))
    # asyncio.get_event_loop().run_until_complete(trainer.connect())


if __name__ == "__main__":
    main()
