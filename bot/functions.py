import inspect
import re
import numpy as np
from functools import reduce
from collections import defaultdict
from cytoolz.dicttoolz import merge_with

import pyastar

from bot.config import Bot


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


def get_player_positions(char_info, with_power_ups=False):
    def do(item):
        if with_power_ups:
            if item["carryingPowerUp"]:
                return item["position"]
            return None
        return item["position"]

    return list(filter(lambda i: i, map(do, char_info)))


def unzip(list_of_dicts):
    return merge_with(list, *list_of_dicts)


def to1d(x: int, y: int, width: int):
    return x + width * y


def to2d(i: int, width: int):
    return i % width, i // width


def idx_2d_within(shape, xy, d=4):
    x = np.arange(shape[1])
    y = np.arange(shape[0])
    mask = abs(x[np.newaxis, :] - xy[1]) + abs(y[:, np.newaxis] - xy[0]) < d

    idx = np.argwhere(mask)
    return idx


def furthest_point(shape, xy, obstacle_positions):
    x = np.arange(shape[1])
    y = np.arange(shape[0])
    mask = abs(x[np.newaxis, :] - xy[1]) + abs(y[:, np.newaxis] - xy[0])
    mask[list(map(lambda i: to2d(i, shape[0]), obstacle_positions))] = 0
    idx = np.argmax(mask)
    return idx


def get_our_bot(char_info):
    for char in char_info:
        if char["name"] == Bot.name:
            return char


def get_plan(state_map):
    character_infos, height, width, power_up_positions, obstacle_positions = pluck(state_map)

    OBS_HIT_PENALTY = 50
    POWERUP_HIT_PENALTY = 10
    ALREADY_MY_COLOR_PENALTY = 5

    grid_shape = (width, height)

    player_positions = get_player_positions(character_infos)

    opponents_with_powerup_positions = get_player_positions(character_infos, with_power_ups=True)

    weights = np.ones(grid_shape, dtype=np.float32).flatten()

    weights[obstacle_positions] += OBS_HIT_PENALTY
    weights[player_positions] += OBS_HIT_PENALTY

    our_bot = get_our_bot(character_infos)

    if len(opponents_with_powerup_positions) != 0:
        for opponent in map(lambda i: to2d(i, width), opponents_with_powerup_positions):
            affected_area = list(map(lambda p: to1d(*p, width), idx_2d_within(grid_shape, opponent)))
            weights[affected_area] += POWERUP_HIT_PENALTY

    weights[our_bot["colouredPositions"]] += ALREADY_MY_COLOR_PENALTY

    goals = power_up_positions

    goals += [furthest_point(grid_shape, to2d(our_bot["position"], width), obstacle_positions)]

    best_cost = np.inf

    best_path = [to2d(our_bot["position"], width)]

    weights = weights.reshape(grid_shape)

    chosen_goal = None
    for goal in goals:
        path = pyastar.astar_path(weights, to2d(our_bot["position"], width), to2d(goal, width))
        cost = len(path)
        if cost > best_cost:
            best_path = path
            best_cost = cost
            chosen_goal = goal

    return best_path, goal
