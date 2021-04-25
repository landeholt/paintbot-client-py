import asyncio
import logging
import websockets
import orjson as json

from config import Config, Message
from bot.config import GAME_SETTINGS

from typing import Callable, Union

logging.basicConfig(level=logging.INFO)


messageSwitch = {
    Message.HeartbeatResponse: 
}

async def message_handler(bot: Callable, ws: websockets.WebSocketClientProtocol) -> None:
    data: Union[str, bytes]
    async for data in ws:
        message = json.loads(data)


def create_client(
    bot: Callable,
    on_game_ready: Callable,
    game_settings: GAME_SETTINGS,
    host: str = Config.host,
    venue: str = Config.venue,
) -> None:

    uri = host + venue
    async with websockets.connect(uri) as ws:
        await message_handler(bot, ws)
