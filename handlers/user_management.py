from vkbottle.bot import Message
from loader import bot, evg
from utils.custom_rules import Command, CommandWithAnyArgs, InteractionUsers
from db_api.db_engine import db
from utils.parsing import parse_cooldown
import time
from decimal import Decimal
from utils.parsing_users import get_register_date
from config import DATE_PARSING
from vkbottle import Keyboard, KeyboardButtonColor, Callback, OpenLink, GroupEventType
from vkbottle_types.events.bot_events import MessageEvent


@bot.on.message(Command("профиль"))
@bot.on.message(Command("кто я"))
@bot.on.message(Command("ктоя"))
@bot.on.message(Command("обо мне"))
@bot.on.message(InteractionUsers("кто ты", offset=1, return_himself=True))
async def user_profile(m: Message, to_user_id: int = None):
    if not to_user_id:
        to_user_id = m.from_id
    name, nickname, ext_nick, boost_kombucha, balance, kombucha, kombucha_time, description, screen_plus = await (
        db.select([db.User.names[1], db.User.nickname, db.User.ext_nick, db.User.boost_kombucha, db.User.balance,
                   db.User.kombucha, db.User.kombucha_date, db.User.description, db.User.screen_plus]).where(
            db.User.user_id == to_user_id)
    ).gino.first()
    kombucha = Decimal(kombucha).quantize(Decimal("1.000"))
    kombucha_time = time.mktime(kombucha_time.timetuple())
    rp_commands = await db.select([db.func.count()]).where(db.RPCommand.owner == to_user_id).gino.scalar()
    register_date = await get_register_date(to_user_id)
    reply = f"✋ Приветствую тебя, [id{to_user_id}|{name}]!\n\n" \
            f"👲 Твой никнейм: {nickname if nickname is not None else ''}\n" \
            f"👑 Возможность устанавливать расширенный ник: {'есть ✅' if ext_nick else 'нету ❌'}\n" \
            f"🛡 Защита от уменьшения гриба при рандоме: {'есть ✅' if boost_kombucha else 'нету ❌'}\n" \
            f"💰 На счету: {balance}🧊\n" \
            f"🎥 Команда скрин+: {'есть ✅' if screen_plus else 'нету ❌'}\n" \
            f"🍄 Рост гриба: {kombucha} см\n" \
            f"⌚ Рандом гриба доступен через: " \
            f"{'сейчас' if (time.time() - kombucha_time) > 10800 else parse_cooldown(kombucha_time + 10800 - int(time.time()))}\n" \
            f"🌈 Количество рп команд: {rp_commands if rp_commands > 0 else 'пока нету'} штук\n" \
            f"📄 Дата регистрации: {register_date.strftime(DATE_PARSING) if register_date else 'неизвестна'}\n"
    if m.peer_id > 2000000000:
        invited_by, joined_at = await (
            db.select([db.UserToChat.invited_by, db.UserToChat.joined_at]).where(db.UserToChat.user_id == to_user_id).gino.first()
        )
        if invited_by > 0:
            invited_by_nickname, invited_by_name = await db.select([db.User.nickname, db.User.names[1]]).where(db.User.user_id == invited_by).gino.first()
        else:
            invited_by_nickname = None
            invited_by_name = (await evg.api.groups.get_by_id(group_id=abs(invited_by)))[0].name
        reply += f"🤵 Пригласил{'a' if await db.is_woman_user(invited_by) else ''} " \
                 f"[{'club' if invited_by < 0 else 'id'}{invited_by}|{invited_by_nickname or invited_by_name}]\n" \
                 f"👴 В беседе с {joined_at.strftime('%d.%m.%Y %H:%M:%S')}\n"
    reply += f"✏ Описание: {description if description is not None else ''}\n"
    await bot.reply_msg(m, reply)


@bot.on.message(CommandWithAnyArgs("описание "))
@bot.on.message(CommandWithAnyArgs("описание\n"))
async def set_description(m: Message):
    description = m.text[9:]
    await db.User.update.values(description=description).where(db.User.user_id == m.from_id).gino.status()
    await bot.reply_msg(m, f"Теперь ваше описание: «{description}»")


@bot.on.message(Command("купить ник+"))
async def buy_vip(m: Message):
    balance = await db.User.select('balance').where(db.User.user_id == m.from_id).gino.scalar()
    if balance >= 15:
        await (db.User.update.values(ext_nick=True, balance=db.User.balance - 15)
               .where(db.User.user_id == m.from_id)).gino.status()
        await bot.reply_msg(m, "🎉 Супер! Теперь ты можешь ставить в ник любые символы, а также твой ник расширен до "
                              "30 символов")
        return
    await bot.reply_msg(m, f"🪫 Для покупки расширенного ника нужно 15 кубиков сахара 🧊. У вас доступно {balance} 🧊\n"
                          f"Чтобы пополнить баланс введите «пополнить баланс»")


@bot.on.message(Command("купить скрин+"))
async def buy_vip(m: Message):
    balance = await db.User.select('balance').where(db.User.user_id == m.from_id).gino.scalar()
    if balance >= 40:
        await (db.User.update.values(ext_nick=True, balance=db.User.balance - 40)
               .where(db.User.user_id == m.from_id)).gino.status()
        await bot.reply_msg(m, "🎉 Супер! Теперь ты можешь использовать команду «скрин+»")
        return
    await bot.reply_msg(m, f"🪫 Для покупки расширенной команды скрин нужно 40 кубиков сахара 🧊. У вас доступно {balance} 🧊\n"
                          f"Чтобы пополнить баланс введите «пополнить баланс»")


@bot.on.message(Command("купить защиту"))
async def buy_defend(m: Message):
    balance = await db.User.select('balance').where(db.User.user_id == m.from_id).gino.scalar()
    if balance >= 15:
        await db.User.update.values(boost_kombucha=True, balance=db.User.balance - 15).where(
            db.User.user_id == m.from_id
        ).gino.status()
        await bot.reply_msg(m, "🎉 Супер! Теперь у тебя не будет уменьшаться гриб при рандоме")
        return
    await bot.reply_msg(m, f"🪫 Для покупки защиты от уменьшения нужно 15 кубиков сахара 🧊. У тебя доступно {balance} 🧊\n"
                          "Чтобы пополнить баланс введите «пополнить баланс {сумма}»")


@bot.on.message(text="пополнить баланс <amount:int>")
async def buy_sugar(m: Message, amount: int = None):
    from loader import qiwi
    bill = await qiwi.bill(amount=amount, lifetime=15, comment=f"{m.from_id}")
    url = f"http://195.133.1.178/qiwiredirect?invoice_uid={bill.pay_url[-36:]}"
    kb = Keyboard(inline=True).add(OpenLink(url, "Оплатить", {"bill_redirect": bill.bill_id}),
                                   KeyboardButtonColor.SECONDARY)
    kb.row()
    kb.add(Callback("Проверить оплату", {"bill_check": bill.bill_id}), KeyboardButtonColor.SECONDARY)
    await bot.reply_msg(m, "Счёт для оплаты создан, оплатите в течении 15 минут", keyboard=kb)


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, blocking=False)
async def confirm_buy_sugar(m: MessageEvent):
    if "bill_check" not in m.object.payload:
        return
    from loader import qiwi
    bill_id: int = m.object.payload['bill_check']
    bill = await qiwi.check(bill_id)
    if bill.status != "PAID":
        await bot.send_ans(m, "Счёт не оплачен")
        return
    await db.User.update.values(balance=db.User.balance+int(float(bill.amount))).where(
        db.User.user_id == int(bill.comment)).gino.status()
    await bot.change_msg(m, "🎉 Баланс успешно пополнен!")
