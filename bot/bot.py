from bot.config import Actions
from bot.functions import get_plan


from collections import deque
import traceback


coord2action = {
    (0, 0): Actions.stay,
    (0, 1): Actions.left,
    (0, -1): Actions.right,
    (-1, 0): Actions.down,
    (1, 0): Actions.up,
}


class Bot:
    def __init__(self):
        self.plan = deque()
        self.goal = None
        self.last_pos = None
        self.tick = 0
        self.one_time = True

    def get_next_action(self, kwargs):
        self.tick += 1
        try:
            # 1. Find a suitable path. Preferably to a power up
            # 2. use powerup (explode)
            # 3. use powerup to stun opponents
            # 4. award repainting opponents tiles high?
            # 5. avoid opponent explosions
            # 6. avoid obstacles
            plan, goal = get_plan(kwargs["map"])

        except Exception as e:
            # pass
            print(traceback.format_exc())


def create_bot():

    return Bot()
