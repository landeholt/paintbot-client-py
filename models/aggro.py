import numpy as np
from bot.config import PARAMS

from functools import reduce

from typing import List, Callable, Dict

parameters = PARAMS(
    OBS_HIT_PENALTY=7000,
    OPPONENT_HIT_PENALTY=120,
    POWERUP_HIT_PENALTY=20,
    ALREADY_MY_COLOR_PENALTY=10,
    OPPONENT_COLOUR_BONUS=60,
    POWERUP_BONUS=40,
    PROBABILITY_AREA=20,
    STUCK_POLICY=0,
)

from bot.functions import to1d, to2d, idx_2d_within, get_coloured_positions, get_points


def render_weights(weights: np.array, **kwargs):

    grid_shape = kwargs.get("grid_shape", ())
    obstacle_positions = kwargs.get("obstacle_positions", [])
    powerup_positions = kwargs.get("powerup_positions", [])
    opponent_bots = kwargs.get("opponent_bots", [])
    our_bot = kwargs.get("our_bot", {})

    ### Helper functions

    def opponent_mask(position2d: np.array, distance: int = 4):
        x, y = np.arange(grid_shape[1]), np.arange(grid_shape[0])

        mask = abs(x[np.newaxis, :] - position2d[1]) + abs(y[:, np.newaxis] - position2d[0])
        distance_mask = mask >= distance
        mask[distance_mask] = 0
        mask = 1 / np.power(2, mask)
        mask[distance_mask] = 0
        return mask.flatten()

    def avoidance_mask(opponent):
        position1d = opponent["position"]
        position2d = to2d(position1d, grid_shape)
        mask = opponent_mask(position2d, distance=parameters.PROBABILITY_AREA)
        return parameters.OPPONENT_HIT_PENALTY * mask * (1 + int(opponent["carryingPowerUp"]) * 4)

    def eval_bonus(position1d):
        position2d = to2d(position1d, grid_shape)
        explode_radius = 5

        affected_indices = idx_2d_within(grid_shape, position2d, d=explode_radius)
        bonus = len(affected_indices)
        return bonus

    def sum_points(acc, it):
        return acc + get_points(it)

    ### weight mutable functions

    def obstacle_avoidance(weights):
        weights[obstacle_positions] += parameters.OBS_HIT_PENALTY

    def opponent_avoidance(weights):
        # weights += np.concatenate(list())
        for avoiding_box in map(avoidance_mask, opponent_bots):
            weights += avoiding_box

    def powerup_bonus(weights):
        for position, bonus in zip(powerup_positions, map(eval_bonus, powerup_positions)):
            weights[position] -= bonus

    def avoid_our_coloured_positions(weights):
        our_tiles = get_coloured_positions(our_bot)
        weights[our_tiles] += parameters.ALREADY_MY_COLOR_PENALTY

    def recolour_opponent_positions(weights):
        total_score = reduce(sum_points, opponent_bots, 1e-6)
        opponent_scores = np.array(list(map(get_points, opponent_bots)))
        leading_opponent = np.max(opponent_scores) + 1e-6

        weighted_opponent_scores = (opponent_scores / leading_opponent) ** 2
        weighted_opponent_scores -= np.min(weighted_opponent_scores) + 1

        for score, opponent in zip(weighted_opponent_scores, opponent_bots):
            positions = get_coloured_positions(opponent)
            weights[positions] -= parameters.OPPONENT_COLOUR_BONUS * score

    [
        fn(weights)
        for fn in [
            obstacle_avoidance,
            opponent_avoidance,
            powerup_bonus,
            avoid_our_coloured_positions,
            recolour_opponent_positions,
        ]
    ]
