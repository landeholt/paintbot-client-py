import asyncio
import logging
import inspect
import re
import sys


from client.config import Config, Message, prompt_style
from bot.config import Bot
from client.exceptions import UnsupportedGameMode, InvalidPlayer, GameOver

from typing import Optional, Callable
from dataclasses import dataclass
from PyInquirer import prompt
from pprint import pformat

import websockets.exceptions as wse

from functools import reduce

logger = logging.getLogger(__name__)


def print_replace(message):
    # sys.stdout.write("\n")
    sys.stdout.write(f"{message}\r")
    sys.stdout.flush()


def pluck(_dict: dict, to_snake=True):
    def get_upper(match: re.Match) -> str:
        return match.group(0)[1].upper()

    def as_camel(key: str) -> str:
        return re.sub(r"_\w", get_upper, key)

    def generator(_dict: dict, keys: list):
        for key in keys:
            yield _dict[key]

    if not isinstance(_dict, dict):
        raise TypeError(f"{_dict} is not a dict")
    frame = inspect.currentframe().f_back
    (ctx,) = inspect.getframeinfo(frame).code_context
    variables, function_call = ctx.split(" = ")

    if to_snake:
        keys = [as_camel(k.strip()) for k in variables.split(",")]
    else:
        keys = [k.strip() for k in variables.split(",")]

    if missing := [key for key in keys if key not in _dict]:
        raise KeyError(*missing)

    if len(keys) == 1:
        (key,) = keys
        return _dict[key]
    else:
        return generator(_dict, keys)


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


async def heartbeat_response(kwargs: dict, bot=None) -> dict:

    try:
        receiving_player_id = pluck(kwargs)
        # await asyncio.sleep(Config.HEARTBEAT_INTERVAL)
        return create_heartbeat_request_message(receiving_player_id)
    except:
        pass


async def player_registered(kwargs: dict, bot=None) -> dict:
    try:
        receiving_player_id, game_mode, game_settings = pluck(kwargs)
        Config.mutable.latest_game_mode = game_mode
        Config.mutable.latest_game_settings = game_settings

        bot.set_settings(game_settings)

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
    log(logger.error, f"The player name {Bot.name} was invalid")
    raise InvalidPlayer


async def game_link(kwargs: dict, bot=None) -> dict:
    try:
        url = pluck(kwargs)
        game_link = url
        log(logger.info, "Game is ready")
        Config.mutable.latest_game_link = game_link
        if Config.auto_start and Config.mutable.latest_game_mode == Config.game_mode.training:
            return create_game_message()

        return on_game_ready(create_game_message)
    except GameOver as exc:
        raise exc
    except Exception as exc:
        print(exc)
        pass


async def game_starting(kwargs: dict, bot=None) -> None:
    log(logger.info, "Game is starting...")


async def game_result(kwargs: dict, bot=None) -> None:
    log(logger.info, "Game result is in")


async def game_ended(kwargs: dict, bot=None) -> dict:
    try:
        player_winner_name = pluck(kwargs)
        log(logger.warn, f"You can view the game at {Config.mutable.latest_game_link}")
        if player_winner_name:
            log(logger.info, f"Game has ended. The winner was {player_winner_name}")
        if Config.mutable.latest_game_mode == Config.game_mode.training:
            await bot.save()
            raise GameOver
    except GameOver as exc:
        raise exc
    except:
        pass


async def tournament_ended(kwargs: dict, bot=None):
    print("Tournament ended!!")
    raise GameOver


async def map_update(kwargs: dict, bot=None) -> dict:
    try:
        game_tick, receiving_player_id, game_id = pluck(kwargs)
        action = bot.get_next_action(kwargs)

        log_game_progress(game_tick)

        return create_register_move_message(action, receiving_player_id, game_id, game_tick)
    except:
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