from vkbottle import Keyboard, Callback, KeyboardButtonColor


def user_left_kb(user_id: int) -> "Keyboard":
    kb = Keyboard(inline=True, one_time=False)
    kb.add(Callback("Кикнуть!", {"kick_user": user_id}), KeyboardButtonColor.NEGATIVE)
    return kb
