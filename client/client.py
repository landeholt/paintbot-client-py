import asyncio
import logging
import websockets
import orjson as json
import pathlib
import ssl

from client.config import Config, Message, client_info
from client.exceptions import GameOver
from bot.config import GAME_SETTINGS, Bot
from client.functions import dispatcher

from typing import Callable, Union

logger = logging.getLogger(__name__)


async def dispatch(message_type: str, message: dict, bot) -> dict:
    return await dispatcher[message_type](message, bot)


async def bot_register(send_message: Callable) -> None:
    logger.info("WebSocket is open")
    await send_message(client_info)
    logger.info(f"Registering player {Bot.name}")
    await send_message(
        {
            "type": Message.RegisterPlayer,
            "playerName": Bot.name,
            "gameSettings": GAME_SETTINGS(),
        },
    )


def dumps(message: dict) -> str:
    # Paintbot Server apparently only allows Text-Frames
    return json.dumps(message).decode()


async def message_handler(ws: websockets.WebSocketClientProtocol, bot) -> None:
    async def send_message(message: dict) -> None:
        await ws.send(dumps(message))

    await bot_register(send_message)

    data: Union[str, bytes]
    async for data in ws:
        try:
            message: dict = json.loads(data)

            message_type: str = message["type"]
            response = await dispatch(message_type, message, bot)
            if response:
                await send_message(response)

        except websockets.exceptions.InvalidState:
            return
        except GameOver:
            return


async def create_client(
    bot,
    host: str = Config.host,
    venue: str = Config.venue,
) -> None:

    uri = f"{host}/{venue}"

    async with websockets.connect(uri) as ws:
        await message_handler(ws, bot)
