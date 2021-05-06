import asyncio
import logging
import sys

import os
import subprocess

from client import client, functions as fns
from client.config import Message, prompt_style, Config
from bot.bot import create_bot
from bot.config import Bot as Bot_config

# from trainer import trainer

from pprint import pformat

FIRST_MESSAGE = True


def middleware(message: dict) -> dict:
    global FIRST_MESSAGE
    middleware.hook_type = "test"
    if message["type"] == Message.MapUpdate and FIRST_MESSAGE and message["gameTick"] == 125:
        FIRST_MESSAGE = False
        # fns.print_replace(message)

    return message


def setup():
    from PyInquirer import prompt

    questions = [
        {
            "type": "list",
            "name": "model",
            "message": "Choose model",
            "choices": ["aggro"],
            "default": "aggro",
        },
        {
            "type": "input",
            "name": "botname",
            "message": "Choose botname",
            "default": "Pythonista",
        },
        {
            "type": "confirm",
            "name": "autostart",
            "message": "Want to autostart match?",
            "default": True,
        },
        {
            "type": "list",
            "name": "venue",
            "message": "Which type of venue?",
            "choices": ["Local Training", "Local Tournament", "Live Training", "Live Tournament"],
            "default": "Local Training",
        },
        {"type": "confirm", "name": "save_gif", "message": "want to save a replay?", "default": False},
        {"type": "confirm", "name": "open_game_link", "message": "auto open game?", "default": False},
    ]
    args = prompt(questions, style=prompt_style)

    if "Local" in args["venue"]:
        host = "ws://localhost:8080"
    else:
        host = "wss://server.paintbot.cygni.se"

    if "Training" in args["venue"]:
        venue = "training"
    else:
        venue = "tournament"

    client_config = Config(
        host=host, venue=venue, auto_start=args["autostart"], open_game_link=args["open_game_link"]
    )
    bot_config = Bot_config(name=args["botname"], save_gif=args["save_gif"], model=args["model"])
    return client_config, bot_config


def main():
    logging.basicConfig(level=logging.INFO)

    client_config, bot_config = setup()

    if "localhost" in client_config.host and client_config.venue == "tournament":
        processes = []
        for model in ["aggro" * 3]:
            p = subprocess.Popen(f"python bot_runner.py {model}", shell=True)
            processes.append(p)

        exit_codes = [p.wait() for p in processes]
    else:
        bot = create_bot(bot_config)

        asyncio.get_event_loop().run_until_complete(
            client.create_client(
                bot, host=client_config.host, venue=client_config.venue, middlewares=[middleware]
            )
        )


if __name__ == "__main__":
    main()
