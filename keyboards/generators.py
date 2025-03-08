from vkbottle import Keyboard, Callback, KeyboardButtonColor, Text

from db_api.db_engine import db


def user_left_kb(user_id: int) -> "Keyboard":
    kb = Keyboard(inline=True, one_time=False)
    kb.add(Callback("Кикнуть!", {"kick_user": user_id}), KeyboardButtonColor.NEGATIVE)
    return kb


def get_bets(player: bool):
    bets = Keyboard().add(
        Text("100 💸", {"roulette_bet": 100, "player": player}), KeyboardButtonColor.PRIMARY
    ).add(
        Text("250 💸", {"roulette_bet": 250, "player": player}), KeyboardButtonColor.PRIMARY
    ).add(
        Text("500 💸", {"roulette_bet": 500, "player": player}), KeyboardButtonColor.PRIMARY
    ).add(
        Text("1K 💸", {"roulette_bet": 1000, "player": player}), KeyboardButtonColor.PRIMARY
    ).row().add(
        Text("2.5K 💸", {"roulette_bet": 2500, "player": player}), KeyboardButtonColor.PRIMARY
    ).add(
        Text("5K 💸", {"roulette_bet": 5000, "player": player}), KeyboardButtonColor.PRIMARY
    ).add(
        Text("10K 💸", {"roulette_bet": 10000, "player": player}), KeyboardButtonColor.PRIMARY
    ).add(
        Text("25K 💸", {"roulette_bet": 25000, "player": player}), KeyboardButtonColor.PRIMARY
    ).row().add(
        Text("50K 💸", {"roulette_bet": 50000, "player": player}), KeyboardButtonColor.PRIMARY
    ).add(
        Text("100K 💸", {"roulette_bet": 100000, "player": player}), KeyboardButtonColor.PRIMARY
    ).add(
        Text("250K 💸", {"roulette_bet": 250000, "player": player}), KeyboardButtonColor.PRIMARY
    ).add(
        Text("500K 💸", {"roulette_bet": 500000, "player": player}), KeyboardButtonColor.PRIMARY
    ).row().add(
        Text("1M 💸", {"roulette_bet": 1000000, "player": player}), KeyboardButtonColor.PRIMARY
    ).add(
        Text("2.5M 💸", {"roulette_bet": 250000, "player": player}), KeyboardButtonColor.PRIMARY
    ).add(
        Text("5M 💸", {"roulette_bet": 5000000, "player": player}), KeyboardButtonColor.PRIMARY
    ).add(
        Text("10M 💸", {"roulette_bet": 10000000, "player": player}), KeyboardButtonColor.PRIMARY
    ).row().add(
        Text("Назад", {"main_menu": "roulette"}), KeyboardButtonColor.NEGATIVE
    )
    return bets


def roulette_game(game_id):
    return Keyboard().add(
            Text("Выпить самому", {"game_id": game_id, "drink": 1}), KeyboardButtonColor.POSITIVE
        ).row().add(
            Text("Напоить бота", {"game_id": game_id, "drink": 2}), KeyboardButtonColor.NEGATIVE
        )


async def main_kb(user_id: int):
    main_kb = Keyboard()

    glue_mode = await db.select([db.User.glue_mode]).where(db.User.user_id == user_id).gino.scalar()
    if glue_mode:
        main_kb.add(Text("🤖🧠 Распознавание изображений", {"main_menu": "ai_mode"}), KeyboardButtonColor.NEGATIVE)
    else:
        main_kb.add(Text("🛠 Склеить мем", {"main_menu": "glue"}), KeyboardButtonColor.POSITIVE)

    main_kb.row()
    main_kb.add(Text("🍵☕ Чайная рулетка", {"main_menu": "roulette"}), KeyboardButtonColor.PRIMARY)
    main_kb.add(Text("🔮 Узнать предсказание", {"button": "get_prediction"}), KeyboardButtonColor.PRIMARY)
    main_kb.row()
    main_kb.add(Text("🍵 Получить эстетику", {"button": "get_aesthetic"}), KeyboardButtonColor.PRIMARY)
    main_kb.add(Text("🆘 Команды", {"button": "help"}), KeyboardButtonColor.PRIMARY)
    main_kb.row()
    main_kb.add(Text("♻ Сброс контекста", {"button": "reset_context"}), KeyboardButtonColor.SECONDARY)

    return main_kb
