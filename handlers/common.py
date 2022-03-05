from blueprints.blueprint import bp
from vkbottle.bot import Message
import asyncio
from middlewares.registration import registered_chats
from vkbottle.dispatch.rules.base import PayloadRule
from random import choice, randint


tea_keys = [x.strip() for x in open("teakeys.txt", "r", encoding="utf-8").readlines()]
fortune_keys = [x.strip() for x in open("fortunekeys.txt", "r", encoding="utf-8").readlines()]
means_predict = [x.strip() for x in open("means.txt", "r", encoding="utf-8").readlines()]
figures = [x.strip() for x in open("figures.txt", "r", encoding="utf-8").readlines()]


@bp.on.message(text="бот")
async def echo(m: Message):
    await bp.reply_msg(m, "На месте")


@bp.on.message(text="чай")
async def echo_tea(m: Message):
    await bp.reply_msg(m, "Топ")


@bp.on.private_message(PayloadRule({"button": 5}))
@bp.on.private_message(PayloadRule({"button": "5"}))
@bp.on.private_message(PayloadRule({"button": "help"}))
@bp.on.message(text=["чай помоги", "чай команды", "команды", "помощь", "список команд"])
async def send_help(m: Message):
    await bp.reply_msg(m, "Список команд:", attachment="article-201071106_56737_9267e7523067b92cd6")


@bp.on.message(text="заварить чай")
async def brew_tea(m: Message):
    await bp.reply_msg(m, "⏰ Через 3 минуты твой чай заварится")
    await asyncio.sleep(180)
    chat_db = registered_chats[m.chat_id]
    user_name = await chat_db.get_mention_user(m.from_id, 0)
    await bp.write_msg(m.peer_id, f"🍵 {user_name}, ваш чай заварился", disable_mentions=False)


@bp.on.private_message(PayloadRule({"button": 4}))
@bp.on.private_message(PayloadRule({"button": "4"}))
@bp.on.private_message(PayloadRule({"button": "get_aesthetic"}))
@bp.on.message(text=["чай эстетика", "получить эстетику", "эстетика", "чайная эстетика"])
async def aesthetic(m: Message):
    await bp.reply_msg(m, "Вот твоя эстетика:", attachment=choice(tea_keys))


@bp.on.private_message(PayloadRule({"button": "get_prediction"}))
@bp.on.private_message(PayloadRule({"button": 3}))
@bp.on.private_message(PayloadRule({"button": "3"}))
@bp.on.message(text=["предсказание", "чай предсказание", "получить предсказание"])
async def prediction(m: Message):
    number = randint(0, len(fortune_keys)-1)
    await bp.reply_msg(m, f"Вам выпала фигура: {figures[number]}\n"
                          f"Значение: {means_predict[number]}", attachment=fortune_keys[number])


@bp.on.private_message(PayloadRule({"button": "glue"}))
@bp.on.private_message(PayloadRule({"button": "2"}))
@bp.on.private_message(PayloadRule({"button": 2}))
async def need_glue(m: Message):
    await bp.reply_msg(m, "Кидай фотографии")
