from vkbottle import Keyboard, KeyboardButtonColor, Text


main_kb = Keyboard()
main_kb.add(Text("🌱 Чайная мини-игра", {"button": "tea_game"}), KeyboardButtonColor.SECONDARY)
main_kb.row()
main_kb.add(Text("🛠 Склеить мем", {"button": "glue"}), KeyboardButtonColor.POSITIVE)
main_kb.add(Text("🔮 Узнать предсказание", {"button": "get_prediction"}), KeyboardButtonColor.NEGATIVE)
main_kb.row()
main_kb.add(Text("🍵 Получить эстетику", {"button": "get_aesthetic"}), KeyboardButtonColor.PRIMARY)
main_kb.add(Text("🆘 Команды", {"button": "help"}), KeyboardButtonColor.SECONDARY)
