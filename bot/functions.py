import inspect
import re
import numpy as np

import matplotlib.pyplot as plt
from matplotlib import animation

import pyastar
import traceback


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


def plot_state(weights, path, all_goals, powerup_positions):
    plt.figure(figsize=(np.array(weights.shape) / 3))
    plt.imshow(weights, origin="upper", cmap="Greys", interpolation="none")
    plt.scatter(path[0, 1], path[0, 0], marker="o", c="blue", s=100, alpha=0.7)
    plt.scatter(path[-1, 1], path[-1, 0], marker="X", c="white", s=200, alpha=0.9)
    plt.scatter(all_goals[:, 1], all_goals[:, 0], marker="o", c="red", s=200, alpha=0.5)
    if len(powerup_positions) != 0:
        plt.scatter(
            powerup_positions[:, 1],
            powerup_positions[:, 0],
            marker="*",
            c="gold",
            s=200,
            edgecolor="k",
            linewidth=0.7,
        )
    plt.scatter(path[:, 1], path[:, 0], c="blue", s=3)
    plt.show()


def animate_history(history):
    (weights, path, powerup_positions, all_goals, tick) = history[0]
    weights = np.log(weights)
    fig = plt.figure(figsize=(np.array(weights.shape) / 3))

    im1 = plt.imshow(weights, origin="upper", cmap="Greys", interpolation="none")

    im2 = []
    im = plt.scatter(path[:, 1], path[:, 0], c="red", s=20)
    im2.append(im)
    im = plt.scatter(path[0, 1], path[0, 0], marker="o", c="blue", s=100, alpha=0.7)
    im2.append(im)
    im = plt.scatter(path[-1, 1], path[-1, 0], marker="X", c="white", s=200, alpha=0.2)
    im2.append(im)
    im = plt.scatter(all_goals[:, 1], all_goals[:, 0], marker="o", c="red", s=200, alpha=0.5)
    im2.append(im)

    im = plt.title(tick)
    im2.append(im)

    try:
        im = plt.scatter(
            powerup_positions[:, 1],
            powerup_positions[:, 0],
            marker="*",
            c="gold",
            s=200,
            edgecolor="k",
            linewidth=0.7,
        )
        im2.append(im)
    except:
        pass

    def init():
        im1.set_data(weights)
        im2[0].set_offsets(path[:, ::-1])
        im2[1].set_offsets(path[0, ::-1])
        im2[2].set_offsets(path[-1, ::-1])
        im2[3].set_offsets(all_goals[:, ::-1])
        im2[4].set_text(f"{tick}")

        try:
            im2[5].set_offsets(powerup_positions[:, ::-1])

        except:
            pass

    def animate(i):
        (weights, path, powerup_positions, all_goals, tick) = history[i]
        weights = np.log(weights)
        im1.set_data(weights)
        im1.set_clim(vmin=weights.min(), vmax=weights.max())
        im2[0].set_offsets(path[:, ::-1])
        im2[1].set_offsets(path[0, ::-1])
        im2[2].set_offsets(path[-1, ::-1])
        im2[3].set_offsets(all_goals[:, ::-1])
        im2[4].set_text(f"{tick}")

        try:
            im2[5].set_offsets(powerup_positions[:, ::-1])

        except:
            pass

        return im1, im2

    anim = animation.FuncAnimation(fig, animate, init_func=init, frames=len(history), interval=50)
    anim.save(f"video.gif", fps=10)


def to1d(position, shape: tuple):
    return np.ravel_multi_index((position[0], position[1]), shape)


def to2d(i: int, shape: tuple):
    return np.unravel_index(i, shape)


def idx_2d_within(shape, xy, d=5):
    x = np.arange(shape[1])
    y = np.arange(shape[0])
    mask = abs(x[np.newaxis, :] - xy[1]) + abs(y[:, np.newaxis] - xy[0]) < d
    idx = np.argwhere(mask)
    return idx


def furthest_point(shape, xy, obstacle_positions):
    x = np.arange(shape[1])
    y = np.arange(shape[0])
    mask = abs(x[np.newaxis, :] - xy[1]) + abs(y[:, np.newaxis] - xy[0])

    mask = mask.flatten()
    mask[obstacle_positions] = 0
    mask = mask.reshape(shape)
    idx = np.argmax(mask)
    #     idx=np.where(mask==mask.max())
    return to2d(idx, shape)


def get_bots(char_info, config):
    other_bots = []
    our_bot = None
    for char in char_info:
        if char["name"] == config.name:
            our_bot = char
        else:
            other_bots.append(char)
    return our_bot, other_bots


def get_coloured_positions(char_info):
    return char_info["colouredPositions"]


def get_points(char_info):
    return char_info["points"]


def has_power_up(char_info):
    return char_info["carryingPowerUp"]


def is_stunned(char_info, at_tick=9):
    return char_info["stunnedForGameTicks"] <= at_tick


def get_plan(state_map, config, explode_radius, model):
    try:

        character_infos, height, width, power_up_positions, obstacle_positions = pluck(state_map)

        grid_shape = (height, width)

        our_bot, opponent_bots = get_bots(character_infos, config)

        weights = np.ones(grid_shape, dtype=np.float32).flatten()

        model.render_weights(
            weights,
            grid_shape=grid_shape,
            obstacle_positions=obstacle_positions,
            powerup_positions=power_up_positions,
            opponent_bots=opponent_bots,
            our_bot=our_bot,
            explode_radius=explode_radius,
        )

        goals = [
            furthest_point(grid_shape, to2d(our_bot["position"], grid_shape), obstacle_positions)
        ] + list(map(lambda i: to2d(i, grid_shape), power_up_positions))

        best_path = [to2d(our_bot["position"], grid_shape)]
        best_reward = -np.inf

        weights = weights - weights.min() + 1
        weights = weights.reshape(grid_shape)

        for goal in goals:
            path = pyastar.astar_path(weights, to2d(our_bot["position"], grid_shape), goal)

            px, py = list(zip(*path))

            path_length = len(path)
            reward = -weights[px, py].sum()

            if reward > best_reward:
                best_path = path
                best_reward = reward

        chosen_goal = best_path[-1]
        return (
            weights,
            np.array(best_path),
            np.array(power_up_positions),
            np.array(goals),
            has_power_up(our_bot),
            is_stunned(our_bot),
        )
    except Exception as e:
        print(traceback.format_exc())
