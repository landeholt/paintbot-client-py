import asyncio
import logging
import orjson as json
import websockets

from client.config import Config, Message, prompt_style
from bot.config import Bot
from client.exceptions import UnsupportedGameMode, InvalidPlayer, GameOver

from typing import Optional, Callable
from dataclasses import dataclass
from PyInquirer import prompt
from pprint import pformat
import websockets.exceptions as wse

logger = logging.getLogger(__name__)


def log(logger: Callable, message: str) -> None:
    logger(pformat(message, indent=4))


def on_game_ready(start_game: Callable) -> None:
    question = {
        "type": "confirm",
        "message": "Do you want to start the game?",
        "name": "continue",
        "default": True,
    }

    answer = prompt(question, style=prompt_style)
    if answer["continue"]:
        return start_game()
    raise GameOver


def log_game_progress(game_tick: int) -> None:
    if game_tick % 20 == 0:
        duration_in_seconds = Config.mutable.latest_game_settings["gameDurationInSeconds"]
        time_in_ms_per_tick = Config.mutable.latest_game_settings["timeInMsPerTick"]
        total_game_ticks = (duration_in_seconds * 1000) / time_in_ms_per_tick
        progress_in_percent = (game_tick / total_game_ticks) * 100
        log(logger.info, f"Progress: {round(progress_in_percent,1)}%")


def create_heartbeat_request_message(receiving_player_id: str) -> dict:
    return {
        "type": Message.HeartbeatRequest,
        "receivingPlayerId": receiving_player_id,
    }


def create_game_message() -> dict:
    return {"type": Message.StartGame}


def create_register_move_message(action: str, receiving_player_id: str, game_id: str, game_tick: int) -> dict:
    return {
        "type": Message.RegisterMove,
        "direction": action,
        "receivingPlayerId": receiving_player_id,
        "gameId": game_id,
        "gameTick": game_tick,
    }


def dumps(message: dict) -> str:
    # Paintbot Server apparently only allows Text-Frames
    return json.dumps(message).decode()


async def send_message(ws: websockets.WebSocketClientProtocol, message: dict) -> None:
    await ws.send(dumps(message))


async def heartbeat_response(kwargs: dict, bot=None) -> dict:

    try:
        receiving_player_id = kwargs["receivingPlayerId"]

        return create_heartbeat_request_message(receiving_player_id)
    except:
        pass


async def player_registered(kwargs: dict, bot=None) -> dict:
    try:
        receiving_player_id = kwargs["receivingPlayerId"]
        game_mode = kwargs["gameMode"]
        game_settings = kwargs["gameSettings"]
        Config.mutable.latest_game_mode = game_mode
        Config.mutable.latest_game_settings = game_settings

        if game_mode not in Config.SUPPORTED_GAME_MODES:
            raise UnsupportedGameMode

        log(logger.info, f"Player {Bot.name} was successfully registed!")
        log(logger.info, f"Game mode: {game_mode}")
        log(logger.info, f"Game settings: {game_settings}")

        return create_heartbeat_request_message(receiving_player_id)
    except UnsupportedGameMode:
        log(logger.error, f"Unsupported game mode: {game_mode}")
        raise wse.InvalidState


async def invalid_player_name(kwargs: dict, bot=None) -> dict:
    log(logger.info, f"The player name {Bot.name} was invalid")
    raise InvalidPlayer


async def game_link(kwargs: dict, bot=None) -> dict:
    try:
        game_link = kwargs["url"]
        log(logger.info, "Game is ready")
        Config.mutable.latest_game_link = game_link
        if Config.auto_start and Config.mutable.latest_game_mode == Config.game_mode.training:
            return create_game_message()

        return on_game_ready(create_game_message)
    except GameOver as exc:
        raise exc
    except:
        pass


async def game_starting(kwargs: dict, bot=None) -> None:
    log(logger.info, "Game is starting...")


async def game_result(kwargs: dict, bot=None) -> None:
    log(logger.info, "Game result is in")


async def game_ended(kwargs: dict, bot=None) -> dict:
    try:
        log(logger.info, f"You can view the game at {Config.mutable.latest_game_link}")
        if Config.mutable.latest_game_link == Config.game_mode.training:
            log(logger.info, f"Game has ended. The winner was {kwargs.player_winner_name}")
        raise GameOver
    except GameOver as exc:
        raise exc
    except:
        pass


async def tournament_ended(kwargs: dict, bot=None):
    raise GameOver


async def map_update(kwargs: dict, bot=None) -> dict:
    try:
        action = bot.get_next_action(kwargs)
        game_tick = kwargs["gameTick"]
        receiving_player_id = kwargs["receivingPlayerId"]
        game_id = kwargs["gameId"]

        log_game_progress(game_tick)
        return create_register_move_message(action, receiving_player_id, game_id, game_tick)
    except Exception as e:
        print(e)
        pass


dispatcher = {
    Message.HeartbeatResponse: heartbeat_response,
    Message.PlayerRegistered: player_registered,
    Message.InvalidPlayerName: invalid_player_name,
    Message.GameLink: game_link,
    Message.GameStarting: game_starting,
    Message.GameResult: game_result,
    Message.GameEnded: game_ended,
    Message.TournamentEnded: tournament_ended,
    Message.MapUpdate: map_update,
}