import time
from decimal import Decimal

from vkbottle.bot import Message, MessageEvent
from vkbottle import Keyboard, KeyboardButtonColor, Callback, OpenLink, GroupEventType
from ayoomoney.types import PaymentSource, OperationHistoryParams, OperationStatus

from sqlalchemy import and_

from loader import bot, yoomoney
from utils.custom_rules import Command, CommandWithAnyArgs, InteractionUsers
from utils.parsing import parse_cooldown
from utils.parsing_users import get_register_date
from db_api.db_engine import db
from config import DATE_PARSING, DOMAIN, GROUP_TAG


@bot.on.message(Command("профиль"))
@bot.on.message(Command("кто я"))
@bot.on.message(Command("ктоя"))
@bot.on.message(Command("обо мне"))
@bot.on.message(InteractionUsers("кто ты", offset=1, return_himself=True))
async def user_profile(m: Message, to_user_id: int = None):
    if not to_user_id:
        to_user_id = m.from_id
    name, nickname, ext_nick, boost_kombucha, balance, kombucha, kombucha_time, description = await (
        db.select([db.User.names[1], db.User.nickname, db.User.ext_nick, db.User.boost_kombucha, db.User.balance,
                   db.User.kombucha, db.User.kombucha_date, db.User.description]).where(
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
            f"💰 На счету: {balance}🧊\n"\
            f"🍄 Рост гриба: {kombucha} см\n" \
            f"⌚ Рандом гриба доступен через: " \
            f"{'сейчас' if (time.time() - kombucha_time) > 10800 else parse_cooldown(kombucha_time + 10800 - int(time.time()))}\n" \
            f"🌈 Количество рп команд: {rp_commands if rp_commands > 0 else 'пока нету'} штук\n" \
            f"📄 Дата регистрации: {register_date.strftime(DATE_PARSING) if register_date else 'неизвестна'}\n"
    if m.peer_id > 2000000000:
        invited_by, joined_at = await (
            db.select([db.UserToChat.invited_by, db.UserToChat.joined_at]).where(
                and_(db.UserToChat.user_id == to_user_id, db.UserToChat.chat_id == m.chat_id)).gino.first()
        )
        if invited_by > 0:
            invited_by_nickname, invited_by_name = await db.select([db.User.nickname, db.User.names[1]]).where(db.User.user_id == invited_by).gino.first()
        else:
            invited_by_nickname = None
            invited_by_name = (await bot.api.groups.get_by_id(group_id=abs(invited_by))).groups[0].name
        reply += f"🤵 Пригласил{'a' if await db.is_woman_user(invited_by) else ''} " \
                 f"[{'club' if invited_by < 0 else 'id'}{abs(invited_by)}|{invited_by_nickname or invited_by_name}]\n" \
                 f"👴 В беседе с {joined_at.strftime('%d.%m.%Y %H:%M:%S')}\n"
    reply += f"✏ Описание: {description if description is not None else ''}\n"
    await m.reply(reply)


@bot.on.message(CommandWithAnyArgs("описание "))
@bot.on.message(CommandWithAnyArgs("описание\n"))
async def set_description(m: Message):
    description = m.text[9:]
    await db.User.update.values(description=description).where(db.User.user_id == m.from_id).gino.status()
    await m.reply(f"Теперь ваше описание: «{description}»")


@bot.on.message(Command("купить ник+"))
async def buy_vip(m: Message):
    balance = await db.User.select('balance').where(db.User.user_id == m.from_id).gino.scalar()
    if balance >= 15:
        await (db.User.update.values(ext_nick=True, balance=db.User.balance - 15)
               .where(db.User.user_id == m.from_id)).gino.status()
        await m.reply("🎉 Супер! Теперь ты можешь ставить в ник любые символы, а также твой ник расширен до "
                              "30 символов")
        return
    await m.reply(f"🪫 Для покупки расширенного ника нужно 15 кубиков сахара 🧊. У вас доступно {balance} 🧊\n"
                          f"Чтобы пополнить баланс введите «пополнить баланс»")


@bot.on.message(Command("купить защиту"))
async def buy_defend(m: Message):
    balance = await db.User.select('balance').where(db.User.user_id == m.from_id).gino.scalar()
    if balance >= 15:
        await db.User.update.values(boost_kombucha=True, balance=db.User.balance - 15).where(
            db.User.user_id == m.from_id
        ).gino.status()
        await m.reply("🎉 Супер! Теперь у тебя не будет уменьшаться гриб при рандоме")
        return
    await m.reply(f"🪫 Для покупки защиты от уменьшения нужно 15 кубиков сахара 🧊. У тебя доступно {balance} 🧊\n"
                          "Чтобы пополнить баланс введите «пополнить баланс {сумма}»")


@bot.on.message(text="пополнить баланс <amount:int>")
async def buy_sugar(m: Message, amount: int = None):
    message = await m.reply('⌛️ Формируем ссылку для оплаты')
    payment = await db.Payment.create(user_id=m.from_id, peer_id=m.peer_id, cmid=message.conversation_message_id,
                                      amount=amount)
    bill = await yoomoney.create_payment_form(
            amount_rub=amount,
            unique_label=f"Покупка в группе vk.com/{GROUP_TAG} №{payment.id}",
            payment_source=PaymentSource.YOOMONEY_WALLET,
            success_redirect_url=f"https://vk.me/{GROUP_TAG}",
    )
    await db.Payment.update.values(url=bill.link_for_customer).where(db.Payment.id == payment.id).gino.status()
    kb = Keyboard(inline=True).add(OpenLink(f'https://{DOMAIN}/payment?payment_id={payment.id}', "Оплатить",
                                            {"bill_redirect": bill.payment_label}),
                                   KeyboardButtonColor.SECONDARY)
    kb.row()
    kb.add(Callback("Проверить оплату", {"bill_check": bill.payment_label}), KeyboardButtonColor.SECONDARY)
    await bot.api.messages.edit(message="Счёт для оплаты создан, оплатите в течении 15 минут\n\n"
                                        "⚪ Оплачивайте только по той ссылке, которую скинул бот\n\n"
                                        "⚪ При оплате картой советуем использовать Сбер. Другие банки могут взимать "
                                        "комиссию 100 руб.", keyboard=kb,
                                peer_id=message.peer_id, cmid=message.conversation_message_id)


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, blocking=False)
async def confirm_buy_sugar(m: MessageEvent):
    if "bill_check" not in m.object.payload:
        return
    bill_id: int = m.object.payload['bill_check']
    params = OperationHistoryParams(label=bill_id)
    history = await yoomoney.get_operation_history(params)
    if not history or len(history.operations) <= 0:
        status = None
    else:
        status = history.operations[0].status
    if status != OperationStatus.SUCCESS:
        await m.show_snackbar('Счёт не оплачен')
        return
    await m.edit_message("🎉 Баланс успешно пополнен!")
