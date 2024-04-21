from vkbottle import Keyboard, KeyboardButtonColor, Text, Callback

main_kb = Keyboard()
main_kb.add(Text("🍵☕ Чайная рулетка", {"main_menu": "roulette"}), KeyboardButtonColor.PRIMARY)
main_kb.row()
main_kb.add(Text("🛠 Склеить мем", {"button": "glue"}), KeyboardButtonColor.POSITIVE)
main_kb.add(Text("🔮 Узнать предсказание", {"button": "get_prediction"}), KeyboardButtonColor.NEGATIVE)
main_kb.row()
main_kb.add(Text("🍵 Получить эстетику", {"button": "get_aesthetic"}), KeyboardButtonColor.PRIMARY)
main_kb.add(Text("🆘 Команды", {"button": "help"}), KeyboardButtonColor.SECONDARY)

formats = []

formats2 = Keyboard(inline=True, one_time=False)
formats2.add(Callback("Вертикально", {"columns": 1, "upper": 0, "lower": 0}), KeyboardButtonColor.POSITIVE).row()
formats2.add(Callback("Горизонтально", {"columns": 2, "upper": 0, "lower": 0}), KeyboardButtonColor.NEGATIVE)
formats.append(formats2)

formats3 = Keyboard(inline=True, one_time=False)
formats3.add(Callback("1 сверху 2 снизу", {"columns": 2, "upper": 1, "lower": 0}), KeyboardButtonColor.POSITIVE).row()
formats3.add(Callback("2 сверху 1 снизу", {"columns": 2, "upper": 0, "lower": 1}), KeyboardButtonColor.NEGATIVE)
formats.append(formats3)

formats4 = Keyboard(inline=True, one_time=False)
formats4.add(Callback("Плитка 2 на 2", {"columns": 2, "upper": 0, "lower": 0}), KeyboardButtonColor.POSITIVE).row()
formats4.add(Callback("1 сверху 3 снизу", {"columns": 3, "upper": 1, "lower": 0}), KeyboardButtonColor.NEGATIVE).row()
formats4.add(Callback("3 сверху 1 снизу", {"columns": 3, "upper": 0, "lower": 1}), KeyboardButtonColor.PRIMARY)
formats.append(formats4)

formats5 = Keyboard(inline=True, one_time=False)
formats5.add(Callback("2 на 2 + 1 снизу", {"columns": 2, "upper": 0, "lower": 1}), KeyboardButtonColor.POSITIVE).row()
formats5.add(Callback("1 сверху + 2 на 2", {"columns": 2, "upper": 1, "lower": 0}), KeyboardButtonColor.NEGATIVE)
formats.append(formats5)

formats6 = Keyboard(inline=True, one_time=False)
formats6.add(Callback("Плитка 2 на 3", {"columns": 2, "upper": 0, "lower": 0}), KeyboardButtonColor.POSITIVE).row()
formats6.add(Callback("Плитка 3 на 2", {"columns": 3, "upper": 0, "lower": 0}), KeyboardButtonColor.NEGATIVE)
formats.append(formats6)

formats7 = Keyboard(inline=True, one_time=False)
formats7.add(Callback("2 на 3 + 1 снизу", {"columns": 2, "upper": 0, "lower": 1}), KeyboardButtonColor.POSITIVE).row()
formats7.add(Callback("1 сверху + 2 на 3", {"columns": 2, "upper": 1, "lower": 0}), KeyboardButtonColor.NEGATIVE).row()
formats7.add(Callback("3 на 2 + 1 снизу", {"columns": 3, "upper": 0, "lower": 1}), KeyboardButtonColor.PRIMARY).row()
formats7.add(Callback("1 сверху + 3 на 2", {"columns": 3, "upper": 1, "lower": 0}), KeyboardButtonColor.PRIMARY)
formats.append(formats7)

formats8 = Keyboard(inline=True, one_time=False)
formats8.add(Callback("Плитка 2 на 4", {"columns": 4, "upper": 0, "lower": 0}), KeyboardButtonColor.POSITIVE).row()
formats8.add(Callback("Плитка 4 на 2", {"columns": 4, "upper": 0, "lower": 0}), KeyboardButtonColor.NEGATIVE)
formats.append(formats8)

formats9 = Keyboard(inline=True, one_time=False)
formats9.add(Callback("2 на 4 + 1 снизу", {"columns": 2, "upper": 0, "lower": 1}), KeyboardButtonColor.POSITIVE).row()
formats9.add(Callback("1 сверху + 2 на 4", {"columns": 2, "upper": 1, "lower": 0}), KeyboardButtonColor.NEGATIVE).row()
formats9.add(Callback("4 на 2 + 1 снизу", {"columns": 4, "upper": 0, "lower": 1}), KeyboardButtonColor.PRIMARY).row()
formats9.add(Callback("1 сверху + 4 на 2", {"columns": 4, "upper": 1, "lower": 0}), KeyboardButtonColor.SECONDARY).row()
formats9.add(Callback("Плитка 3 на 3", {"columns": 3, "upper": 0, "lower": 0}), KeyboardButtonColor.PRIMARY)
formats.append(formats9)

formats10 = Keyboard(inline=True, one_time=False)
formats10.add(Callback("Плитка 2 на 5", {"columns": 2, "upper": 0, "lower": 0}), KeyboardButtonColor.POSITIVE).row()
formats10.add(Callback("Плитка 5 на 2", {"columns": 5, "upper": 0, "lower": 0}), KeyboardButtonColor.NEGATIVE).row()
formats10.add(Callback("3 на 3 + 1 снизу", {"columns": 3, "upper": 0, "lower": 1}), KeyboardButtonColor.PRIMARY).row()
formats10.add(Callback("1 ссверху + 3 на 3", {"columns": 3, "upper": 1, "lower": 0}), KeyboardButtonColor.SECONDARY)
formats.append(formats10)

boards = Keyboard(inline=True, one_time=False)
boards.add(Callback("Белая рамка", {"boards": True, "color": "white"}), KeyboardButtonColor.POSITIVE).row()
boards.add(Callback("Черная рамка", {"boards": True, "color": "black"}), KeyboardButtonColor.NEGATIVE).row()
boards.add(Callback("Без рамки", {"boards": False, "color": "white"}), KeyboardButtonColor.PRIMARY)


roulette = Keyboard().add(
    Text("Играть с ботом", {"roulette": "bot"}), KeyboardButtonColor.SECONDARY
).row().add(
    Text("Найти игрока", {"roulette": "player"}), KeyboardButtonColor.PRIMARY
).row().add(
    Text("Назад", {"command": "start"}), KeyboardButtonColor.NEGATIVE
)


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
