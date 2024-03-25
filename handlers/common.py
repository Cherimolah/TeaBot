from datetime import datetime, timedelta
from random import choice, randint
from decimal import Decimal, setcontext, Context, ROUND_HALF_UP
import random
import time
import asyncio
import os

from vkbottle.dispatch.rules.base import PayloadRule, PayloadMapRule
from vkbottle.bot import Message, MessageEvent
from vkbottle import Keyboard, Callback, KeyboardButtonColor
from vkbottle import GroupEventType
from sqlalchemy import func
from sqlalchemy.sql import and_
from pyppeteer.errors import TimeoutError
from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientConnectionError

from utils.views import remember_kombucha, generate_text
from loader import bot
from utils.custom_rules import Command, CommandWithAnyArgs
from db_api.db_engine import db
from utils.parsing import get_count_page, parse_cooldown
from keyboards.private import main_kb
from bots.uploaders import bot_photo_message_upl

setcontext(Context(rounding=ROUND_HALF_UP))
screen_users = []


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, PayloadRule({"command": "start"}))
@bot.on.private_message(Command(["меню", "главное меню", "начать", "старт", "start"]))
async def start(m: Message):
    await m.reply("✋ Приветствую тебя! Здесь ты можешь склеить мем, получить эстетику или узнать предсказание",
                       keyboard=main_kb)


@bot.on.message(Command(["бот", "bot"]))
async def echo(m: Message):
    await m.reply("На месте")


@bot.on.message(Command("чай"))
async def echo_tea(m: Message):
    await m.reply("Топ")


@bot.on.private_message(PayloadRule({"button": 5}))
@bot.on.private_message(PayloadRule({"button": "5"}))
@bot.on.private_message(PayloadRule({"button": "help"}))
@bot.on.message(Command(["помоги", "команды", "помощь", "список команд", "help", "commands"]))
async def send_help(m: Message):
    if m.peer_id > 2_000_000_000:
        kb = None
    else:
        kb = main_kb
    await m.reply("Список команд: vk.com/@your_tea_bot-help\n\n"
                  "⚠ Если у тебя есть вопрос по работе бота можешь написать главному админу [id32650977|Илье Елесину] ⚠",
                       attachment="article-201071106_56737_9267e7523067b92cd6", keyboard=kb)


@bot.on.message(Command(["заварить чай", "brew tea"]))
async def brew_tea(m: Message):
    await m.reply("⏰ Через 3 минуты твой чай заварится")
    await asyncio.sleep(180)
    user_name = await db.get_mention_user(m.from_id, 0)
    await bot.api.messages.send(m.peer_id, f"🍵 {user_name}, ваш чай заварился", disable_mentions=False)


@bot.on.private_message(PayloadRule({"button": 4}))
@bot.on.private_message(PayloadRule({"button": "4"}))
@bot.on.private_message(PayloadRule({"button": "get_aesthetic"}))
@bot.on.message(Command(["чай эстетика", "получить эстетику", "эстетика", "чайная эстетика", "aesthetic"]))
async def aesthetic(m: Message):
    photo = await db.Aesthetic.select('photo').order_by(func.random()).limit(1).gino.scalar()
    await m.reply("Вот твоя эстетика:", attachment=photo)


@bot.on.private_message(PayloadRule({"button": "get_prediction"}))
@bot.on.private_message(PayloadRule({"button": 3}))
@bot.on.private_message(PayloadRule({"button": "3"}))
@bot.on.message(Command(["предсказание", "получить предсказание", "prediction", "гадание"]))
async def send_prediction(m: Message):
    prediction = await db.Prediction.query.order_by(func.random()).limit(1).gino.first()
    await m.reply(f"🔮 Вам выпала фигура: {prediction.figure_name}\n"
                          f"📄 Значение: {prediction.mean}", attachment=prediction.picture)


@bot.on.private_message(PayloadRule({"button": "glue"}))
@bot.on.private_message(PayloadRule({"button": "2"}))
@bot.on.private_message(PayloadRule({"button": 2}))
async def need_glue(m: Message):
    await m.reply("Кидай фотографии")


@bot.on.chat_message(Command(["убери клаву", "-клава", "удали клаву", "удали клавиатуру", "убери клавиатуру"]))
async def delete_keyboard(m: Message):
    await m.reply("🗑 Клавиатура удалена!", keyboard=Keyboard())


@bot.on.message(Command(["гриб рандом", "рандом", "random"]))
async def kombucha_rand(m: Message):
    t1: datetime = await db.User.select('kombucha_date').where(db.User.user_id == m.from_id).gino.scalar()
    if (datetime.now() - t1) < timedelta(hours=3):
        await m.reply(f"⏳ Команда доступна каждые 3 часа. Следующий раз можно использовать через "
                              f"{parse_cooldown(int(time.mktime((t1 + timedelta(hours=3)).timetuple()) - time.time()))}")
        return
    if await db.User.select('boost_kombucha').where(db.User.user_id == m.from_id).gino.scalar():
        percent = random.randint(0, 10)
    else:
        percent = random.randint(-10, 10)
    modifier = percent / 100
    komb = await db.User.select('kombucha').where(db.User.user_id == m.from_id).gino.scalar()
    kombucha_old = Decimal(str(komb)).quantize(Decimal("1.000"))
    kombucha = (kombucha_old + kombucha_old * Decimal(str(modifier))).quantize(Decimal("1.000"))
    difference = (kombucha - kombucha_old).quantize(Decimal("1.000"))
    await db.User.update.values(kombucha=kombucha, kombucha_date=datetime.now()).where(
        db.User.user_id == m.from_id
    ).gino.status()
    reply = f"🍄 Твой гриб {'увеличился' if percent >= 0 else 'уменьшился'} на {percent}% или " \
            f"{difference} см\nЕго длина изменилась с {kombucha_old} см на {kombucha} см"
    if percent < 0:
        reply += "\nТы можешь купить защиту от уменьшения гриба при рандоме. Команда «купить защиту»"
    await m.reply(reply)
    asyncio.get_event_loop().create_task(remember_kombucha(m.from_id, 10800))


@bot.on.message(Command(["мой гриб"]))
async def get_my_kombucha(m: Message):
    kombucha = await db.User.select('kombucha').where(db.User.user_id == m.from_id).gino.scalar()
    kombucha = Decimal(kombucha).quantize(Decimal("1.000"))
    await m.reply(f"🍄 Рост твоего гриба составляет {kombucha} см")


@bot.on.message(Command(["все рп команды", "рп команды"]))
async def rp_all_commands(m: Message):
    commands = [x[0] for x in await db.RPCommand.select('command').where(db.RPCommand.owner.is_(None)).gino.all()]
    await m.reply(f"Мои рп-команды в беседах:\n\n{', '.join(commands)}")


@bot.on.message(Command(["все грибы", "список грибов", "рейтинг", "топ грибов", "rating", "грибы топ", "грибы"]))
async def get_kombucha_list(m: Message):
    kombuchas = await (db.User.select('user_id', 'names', 'nickname', 'kombucha')
                       .order_by(db.User.kombucha.desc()).limit(15).offset(0)).gino.all()
    reply = "📝 Список всех грибов:\n\nПоказан общий список грибов. Чтобы посмотреть грибы участников беседы, введите " \
            "«грибы беседы»\n\n"
    count_users = await db.func.count(db.User.user_id).gino.scalar()
    count_pages = get_count_page(count_users, 15)
    if count_users > 15:
        reply += f"Страница 1/{count_pages}\n\n"
    for i, user_info in enumerate(kombuchas):
        user_id, name, nickname, kombucha = user_info
        reply += f"{i + 1}. [id{user_id}|{nickname or name[0]}] {Decimal(kombucha).quantize(Decimal('1.000'))} см\n"
    kb = None
    if count_pages > 1:
        kb = Keyboard(inline=True, one_time=False).add(Callback("➡", {"kombucha_page_total": 2}),
                                                       KeyboardButtonColor.SECONDARY)
    await m.reply(reply, keyboard=kb)


@bot.on.chat_message(Command(["все грибы беседы", "список грибов беседы", "рейтинг беседы", "топ грибов беседы",
                             "rating conf", "грибы топ беседы", "грибы беседы"]))
async def kombucha_list_conf(m: Message):
    kombuchas = await (db.User.select('user_id', 'names', 'nickname', 'kombucha')
                       .select_from(db.User.join(db.UserToChat, db.UserToChat.user_id == db.User.user_id))
                       .where(and_(db.UserToChat.in_chat.is_(True), db.UserToChat.chat_id == m.chat_id))
                       .order_by(db.User.kombucha.desc()).limit(15).offset(0)).gino.all()
    reply = "📝 Список грибов этой беседы:\n\n"
    count_users = await (db.select([db.func.count()])
                         .where(and_(db.UserToChat.in_chat.is_(True), db.UserToChat.chat_id == m.peer_id - 2000000000))
                         .gino.scalar())
    count_pages = get_count_page(count_users, 15)
    if count_users > 15:
        reply += f"Страница 1/{count_pages}\n\n"
    for i, user_info in enumerate(kombuchas):
        user_id, name, nickname, kombucha = user_info
        reply += f"{i + 1}. [id{user_id}|{nickname or name[0]}] {Decimal(kombucha).quantize(Decimal('1.000'))} см\n"
    kb = None
    if count_pages > 1:
        kb = Keyboard(inline=True, one_time=False).add(Callback("➡", {"kombucha_page": 2}),
                                                       KeyboardButtonColor.SECONDARY)
    await m.reply(reply, keyboard=kb)


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, PayloadMapRule({"kombucha_page": int}))
async def get_page_kombucha(m: MessageEvent):
    curr_page = m.payload["kombucha_page"]
    kombuchas = await (db.User.select('user_id', 'names', 'nickname', 'kombucha')
                       .select_from(db.User.join(db.UserToChat, db.UserToChat.user_id == db.User.user_id))
                       .where(and_(db.UserToChat.in_chat.is_(True), db.UserToChat.chat_id == m.peer_id-2000000000))
                       .order_by(db.User.kombucha.desc()).limit(15).offset((curr_page - 1) * 15)).gino.all()
    count_users = await (db.select([db.func.count()])
                         .where(and_(db.UserToChat.in_chat.is_(True), db.UserToChat.chat_id == m.peer_id-2000000000))
                         .gino.scalar())
    count_pages = get_count_page(count_users, 15)
    reply = "📝 Список всех грибов:\n\nПоказан общий список грибов. Чтобы посмотреть грибы участников беседы, введите " \
            f"«грибы беседы»\n\nСтраница {curr_page}/{count_pages}\n\n"
    for i, user_info in enumerate(kombuchas):
        user_id, name, nickname, kombucha = user_info
        reply += f"{(curr_page - 1) * 15 + i + 1}. [id{user_id}|{nickname or name[0]}] {Decimal(kombucha).quantize(Decimal('1.000'))} см\n"
    kb = Keyboard(inline=True, one_time=False)
    if curr_page > 1:
        kb.add(Callback("⬅", {"kombucha_page": curr_page - 1}), KeyboardButtonColor.SECONDARY)
    if curr_page < count_pages:
        kb.add(Callback("➡", {"kombucha_page": curr_page + 1}), KeyboardButtonColor.SECONDARY)
    await m.edit_message( reply, keyboard=kb)


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, PayloadMapRule({"kombucha_page_total": int}))
async def get_page_kombucha(m: MessageEvent):
    curr_page = m.payload["kombucha_page_total"]
    kombuchas = await (db.User.select('user_id', 'names', 'nickname', 'kombucha')
                       .order_by(db.User.kombucha.desc()).limit(15).offset((curr_page - 1) * 15)).gino.all()
    count_users = await db.func.count(db.User.user_id).gino.scalar()
    count_pages = get_count_page(count_users, 15)
    reply = f"📝 Список всех грибов:\n\nСтраница {curr_page}/{count_pages}\n\n"
    for i, user_info in enumerate(kombuchas):
        user_id, name, nickname, kombucha = user_info
        reply += f"{(curr_page - 1) * 15 + i + 1}. [id{user_id}|{nickname or name[0]}] {Decimal(kombucha).quantize(Decimal('1.000'))} см\n"
    kb = Keyboard(inline=True, one_time=False)
    if curr_page > 1:
        kb.add(Callback("⬅", {"kombucha_page_total": curr_page - 1}), KeyboardButtonColor.SECONDARY)
    if curr_page < count_pages:
        kb.add(Callback("➡", {"kombucha_page_total": curr_page + 1}), KeyboardButtonColor.SECONDARY)
    await m.edit_message(reply, keyboard=kb)


@bot.on.message(Command('скрин+'))
@bot.on.message(Command('скрин+ ', null_args=False, returning_args=True, args_names=('url',)))
async def screen_base(m: Message, url: str = None):
    if m.from_id in screen_users:
        await m.reply("⏳ У тебя уже грузится скрин. По одному, пожалуйста")
        return
    screen_plus = await db.select([db.User.screen_plus]).where(db.User.user_id == m.from_id).gino.scalar()
    if not screen_plus:
        await m.reply("🚫 Команда доступна для тех, у кого есть опция скрин+\n\n"
                               "Напиши «купить скрин+»")
        return
    if url is None:
        await m.reply("🤷‍♂️ Нужно добавить ссылку. Пример: «скринб https://vk.com»")
        return
    if not url.startswith("https://") and not url.startswith("http://"):
        url = f"https://{url}"
    await m.reply("🎥 Чайник достаёт свой фотоаппарат")
    async with ClientSession(timeout=ClientTimeout(5)) as session:
        try:
            response = await session.get(url)
        except ClientConnectionError:
            await m.reply("❌ Адрес недоступен!")
        if not str(response.status).startswith('2'):
            await m.reply("❌ Сервер вернул неуспешный ответ!")
            return
    from loader import browser
    page = await browser.newPage()
    await page.setViewport({'width': 1920, 'height': 1080})
    try:
        await page.goto(url, {"timeout": 15*1000, 'waitUntil': 'networkidle0'})
    except TimeoutError:
        pass
    if not os.path.exists(f"data/{m.from_id}"):
        os.mkdir(f"data/{m.from_id}")
    await page.screenshot({'path': f'data/{m.from_id}/screenshot.png'})
    await page.close()
    attachment = await bot_photo_message_upl.upload(f'data/{m.from_id}/screenshot.png')
    os.remove(f'data/{m.from_id}/screenshot.png')
    await m.reply("Держи скрин сайта", attachment=attachment)


@bot.on.message(Command('скрин'))
@bot.on.message(Command('скрин ', null_args=False, returning_args=True, args_names=('url',)))
async def screen_url(m: Message, url: str = None):
    if url is None:
        await m.reply("🤷‍♂️ Нужно добавить ссылку. Пример: «скрин https://vk.com»")
        return
    await m.reply("🎥 Чайник достаёт свой фотоаппарат")
    async with ClientSession() as session:
        response = await session.get(f"https://mini.s-shot.ru/1920x1080/1024/png/?{url}")
        photo = await response.read()
        attachment = await bot_photo_message_upl.upload(photo)
        await m.reply("🔍 Держи скрин сайта\n\nНекоторые сайты не отображаются с прокси сервера. "
                               "Для отправки запросов с основного российского сервера используйте команду "
                               "«скрин+ https://example.com»",
                            attachment=attachment)


@bot.on.message(CommandWithAnyArgs("инфа "))
async def get_chance(m: Message):
    await m.reply(f"🔮 Вероятность этого события составляет {randint(0, 100)}%")


@bot.on.message(CommandWithAnyArgs("выбери "))
async def get_choice(m: Message):
    options = m.text[7:].split(" или ")
    if len(options) <= 1:
        await m.reply("🚫 Выбор должен быть минимум между двумя вариантами. Пример: «выбери красный или бараны»")
        return
    await m.reply(f"⚖ Я выбираю «{choice(options)}»")


@bot.on.message(Command("g"))
@bot.on.message(Command("g ", args_names=("max_chars",), null_args=False, returning_args=True))
async def generate_text_command(m: Message, max_chars=None):
    if not max_chars:
        max_chars = 4096
    try:
        max_chars = int(max_chars)
    except ValueError:
        await m.reply("Неправильно указано максимальное количество символов!\n"
                      "Значение должно быть от 1 до 4096")
        return
    if max_chars < 1 or max_chars > 4096:
        await m.reply("Неправильно указано максимальное количество символов!\n"
                      "Значение должно быть от 1 до 4096")
        return
    await m.reply(await generate_text(max_chars))
