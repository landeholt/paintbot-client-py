from bot.config import Actions
from bot.functions import get_plan, plot_state, animate_history


from collections import deque
import traceback
import logging
import importlib

import numpy as np

from multiprocessing import Process
from dataclasses import dataclass

from client.config import Config as client_config

logger = logging.getLogger(__name__)


c2a = {
    (0, 0): Actions.stay,
    (0, -1): Actions.left,
    (0, 1): Actions.right,
    (1, 0): Actions.down,
    (-1, 0): Actions.up,
    (-1, -1): Actions.explode,
}


class Bot:
    def __init__(
        self,
        config,
    ):
        self.history = []
        self.tick = 0
        self.config = config
        self.last_position = np.array([0, 0])
        self.same_position_counter = 0
        self.last_tick = -1
        self.explode_radius = 4
        try:
            self.model = importlib.import_module(f"models.{config.model}")
        except:
            from models import aggro

            self.model = aggro

    def get_next_action(self, kwargs):
        self.tick += 1
        try:
            weights, plan, power_up_positions, goals, carrying_power_up, is_stunned = get_plan(
                kwargs["map"], self.config, self.explode_radius, self.model
            )
            dx, dy = plan[1] - plan[0]

            if carrying_power_up:
                if self.tick == self.last_tick:
                    return c2a[(-1, -1)]
                if len(plan) <= 3:
                    return c2a[(-1, -1)]

            self.history.append(
                (weights.copy(), plan.copy(), power_up_positions.copy(), goals.copy(), self.tick)
            )
            return c2a[(dx, dy)]

        except Exception as e:
            print(traceback.format_exc())

    async def save(self):
        if self.config.save_gif:
            animate_history(self.history)

    def set_settings(self, game_settings):
        self.last_tick = (
            game_settings["gameDurationInSeconds"] * 1000 / game_settings["timeInMsPerTick"]
        ) - 2
        self.explode_radius = game_settings["explosionRange"]


def create_bot(config):

    return Bot(config)
