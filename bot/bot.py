from bot.config import Actions
import random


def get_next_action(kwargs):
    return random.choice(
        [
            Actions.stay,
            Actions.down,
            Actions.left,
            Actions.up,
            Actions.right,
        ]
    )


def bot():

    bot.get_next_action = get_next_action

    return bot


def create_bot():

    return bot()
