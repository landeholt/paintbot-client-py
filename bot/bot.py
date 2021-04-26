from bot.config import Actions


def get_next_action(kwargs):
    return Actions.stay


def bot():

    bot.get_next_action = get_next_action

    return bot


def create_bot():

    return bot()
