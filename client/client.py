import asyncio
import logging
import websockets
import orjson as json
import pathlib
import ssl

from client.config import Config, Message, client_info
from client.exceptions import GameOver
from bot.config import GAME_SETTINGS, Bot
from client.functions import dispatcher, send_message

from typing import Callable, Union
from dataclasses import asdict

logger = logging.getLogger(__name__)


async def dispatch(message_type: str, message: dict, bot) -> dict:
    return await dispatcher[message_type](message, bot)


async def register(ws, send_message: Callable) -> None:
    logger.info("WebSocket is open")
    await send_message(ws, client_info)
    logger.info(f"Registering player {Bot.name}")
    await send_message(
        ws,
        {
            "type": Message.RegisterPlayer,
            "playerName": Bot.name,
            "gameSettings": GAME_SETTINGS(),
        },
    )


async def delay(ws, send_message: Callable, message):
    await asyncio.sleep(Config.HEARTBEAT_INTERVAL)
    await send_message(ws, message)


async def message_handler(ws: websockets.WebSocketClientProtocol, bot) -> None:

    await register(ws, send_message)

    data: Union[str, bytes]
    async for data in ws:
        try:
            message: dict = json.loads(data)

            message_type: str = message["type"]
            print(message_type)
            response = await dispatch(message_type, message, bot)
            if response:
                if response["type"] == Message.HeartbeatRequest:
                    await asyncio.create_task(delay(ws, send_message, response))
                    continue

                await send_message(ws, response)

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

    # ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    # cert = pathlib.Path(__file__).with_name("ClientCert.crt")
    # ssl_context.load_verify_locations(cert)

    async with websockets.connect(uri) as ws:
        await message_handler(ws, bot)
