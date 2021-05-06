import asyncio
import logging
import websockets
import orjson as json
import pathlib
import ssl
import webbrowser

from client.config import Config, Message, client_info
from client.exceptions import GameOver
from bot.config import GAME_SETTINGS, Bot
from client.functions import dispatcher, print_replace, pluck
from functools import reduce

from types import FunctionType
from typing import Callable, Union
from time import perf_counter

logger = logging.getLogger(__name__)


async def dispatch(message_type: str, message: dict, bot) -> dict:
    return await dispatcher[message_type](message, bot)


async def bot_register(send_message: Callable, bot) -> None:
    logger.debug("WebSocket is open")
    await send_message(client_info)
    logger.debug(f"Registering player {bot.config.name}")
    await send_message(
        {
            "type": Message.RegisterPlayer,
            "playerName": bot.config.name,
            "gameSettings": GAME_SETTINGS(),
        },
    )


def dumps(message: dict) -> str:
    # Paintbot Server apparently only allows Text-Frames
    return json.dumps(message).decode()


def format_time(end, start):
    # logger.warn(f"Messaged recieved and send in: {round((end-start)*1e3,2)}ms")
    print_replace(f"Messaged recieved and send in: {round((end-start)*1e3,2)}ms")


async def message_handler(ws: websockets.WebSocketClientProtocol, bot, middlewares) -> None:
    async def send_message(message: dict) -> None:
        await ws.send(dumps(message))

    def call_middleware(message, fn):
        if isinstance(fn, FunctionType):
            return fn(message)
        return message

    await bot_register(send_message, bot)

    data: Union[str, bytes]
    async for data in ws:
        start_time = perf_counter()
        try:
            message: dict = json.loads(data)
            if middlewares:
                message: dict = reduce(call_middleware, middlewares, message)

            message_type: str = message["type"]
            response = await dispatch(message_type, message, bot)
            if response:
                end_time = perf_counter()
                format_time(end_time, start_time)
                await send_message(response)

        except websockets.exceptions.InvalidState:
            return
        except GameOver:
            """
            def do(acc, it):
                acc.append({"name": it["name"], "points": it["points"]})
                return acc

            _map = message["map"]
            character_infos = pluck(_map)
            # print(sorted(reduce(do, character_infos, []), key=lambda i: i["points"], reverse=True))
            # print()
            """
            return


async def create_client(
    bot, host: str = Config.host, venue: str = Config.venue, open_game_link=False, middlewares=None
) -> None:

    uri = f"{host}/{venue}"

    async with websockets.connect(uri) as ws:
        await message_handler(ws, bot, middlewares)

    try:
        if open_game_link:
            webbrowser.open_new_tab(Config.mutable.latest_game_link)
    except:
        pass