import os
from textwrap import wrap
from decimal import Decimal

from vkbottle.bot import Message, MessageEvent
from loader import bot, evg
from utils.parsing import parse_unix_to_date, get_count_page
from vkbottle import Keyboard, KeyboardButtonColor, Callback
from vkbottle import GroupEventType
from vkbottle.dispatch.rules.base import PayloadMapRule
from config import rangnames, DATE_PARSING
from utils.custom_rules import Command, CommandWithAnyArgs
from db_api.db_engine import db
import re
from sqlalchemy import and_
import aiofiles
from bots.uploaders import bot_doc_message_upl
from utils.custom_rules import InteractionUsers, ChangeSettingsChat
from utils.parsing_users import get_register_date


@bot.on.chat_message(InteractionUsers("предупреждения"))
@bot.on.chat_message(InteractionUsers("преды"))
@bot.on.chat_message(InteractionUsers("варны"))
@bot.on.chat_message(InteractionUsers("warns"))
async def get_warns_command(m: Message, to_user_id: int):
    warns = await (db.select([db.User.user_id, db.User.names[2], db.User.nickname,
                              db.Punishment.created_at, db.Punishment.closing_at])
                   .select_from(db.User.join(db.Punishment, db.Punishment.from_user_id == db.User.user_id))
                   .where(db.Punishment.to_user_id == to_user_id)).gino.all()
    if len(warns) == 0:
        await m.reply(f"✅ У {await db.get_mention_user(to_user_id, 1)} нет предупреждений")
        return
    reply = f"📝 Список предупреждений {await db.get_mention_user(to_user_id, 1)}:\n\n"
    for index, warn in enumerate(warns):
        from_user_id, name, nickanme, from_time, to_time = warn
        reply += f"{index + 1}. От [id{from_user_id}|{nickanme or name}] " \
                 f"с {parse_unix_to_date(from_time)} до {parse_unix_to_date(to_time)}\n"
    await m.reply(reply)


@bot.on.chat_message(Command(["мои варны", "мои преды", "мои предупреждения", "my warns"]))
async def my_warns_command(m: Message):
    await get_warns_command(m, m.from_id)


@bot.on.chat_message(Command(["бан лист", "банлист", "список забаненных", "все баны", "список банов", "баны",
                             "ban list", "bans"]))
async def ban_list_command(m: Message):
    count_ban = await db.select([db.func.count()]).where(
        and_(db.Punishment.type == 3, db.Punishment.chat_id == m.chat_id)).gino.scalar()
    if count_ban == 0:
        await m.reply(f"✅ В беседе отсутствуют забаненные пользователи")
        return
    reply = "📝 Список забаненных пользователей:\n\n"
    if count_ban < 15:
        reply += "\n"
        pages_keyboard = Keyboard()
    else:
        reply += f"Страница 1/{get_count_page(count_ban, 15)}\n\n"
        pages_keyboard = Keyboard(one_time=False, inline=True)
        pages_keyboard.add(Callback("▶", {"ban_page": 2}), KeyboardButtonColor.SECONDARY)
    bans = await (db.select([db.User.user_id, db.User.names[1], db.User.nickname, db.Punishment.closing_at])
                  .select_from(db.User.join(db.Punishment, db.Punishment.to_user_id == db.User.user_id))
                  .where(and_(db.Punishment.chat_id == m.chat_id, db.Punishment.type == 3))
                  .limit(15).offset(0).gino.all())
    for index, ban in enumerate(bans):
        user_id, name, nickname, ban_time = ban
        reply += f"{index + 1}. [id{user_id}|{name if nickname is None else nickname}] до {parse_unix_to_date(ban_time)}\n"
    await m.reply(reply, keyboard=pages_keyboard)


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, PayloadMapRule({"ban_page": int}))
async def handle_message_event(event: MessageEvent):
    curr_page = event.payload['ban_page']
    if event.peer_id < 2000000000:
        return
    count_ban = await db.select([db.func.count()]).where(
        and_(db.Punishment.type == 3, db.Punishment.chat_id == event.peer_id - 2000000000)).gino.scalar()
    count_pages = get_count_page(count_ban, 15)
    reply = f"📝 Список забаненных пользователей:\n\n " \
            f"Страница {curr_page}/{count_pages}\n\n"
    bans = await (db.select([db.User.user_id, db.User.names[1], db.User.nickname, db.Punishment.closing_at])
                  .select_from(db.User.join(db.Punishment, db.Punishment.to_user_id == db.User.user_id))
                  .where(and_(db.Punishment.chat_id == event.peer_id - 2000000000, db.Punishment.type == 3))
                  .limit(15).offset((curr_page - 1) * 15)).gino.all()
    for index, ban in enumerate(bans):
        user_id, name, nickname, ban_time = ban
        reply += f"{(curr_page - 1) * 15 + index + 1}. [id{user_id}|{nickname or name}] {parse_unix_to_date(ban_time)}\n"
    pages_keyboard = Keyboard(one_time=False, inline=True)
    if curr_page > 1:
        pages_keyboard.add(Callback("◀", {"ban_page": curr_page - 1}), KeyboardButtonColor.SECONDARY)
    if curr_page < count_pages:
        pages_keyboard.add(Callback("▶", {"ban_page": curr_page + 1}), KeyboardButtonColor.SECONDARY)
    await event.edit_message(reply, keyboard=pages_keyboard)


@bot.on.chat_message(Command(["админы", "администрация", "правительство", "все админы", "кто админ", "admins"],
                            null_args=True))
async def admins_command(m: Message):
    reply = "📝 Список администраторов беседы:\n\n"
    is_group = await db.select([db.Chat.is_group]).where(db.Chat.chat_id == m.chat_id).gino.scalar()
    if is_group:
        members = await bot.api.messages.get_conversation_members(peer_id=m.peer_id)
        group = await bot.api.groups.get_by_id(group_ids=members.items[0].member_id)
        reply += f"Создатель беседы:\n[club{-group[0].id}|{group[0].name}]\n\n"
    admins = await (db.select([db.User.user_id, db.User.names[1], db.User.nickname, db.UserToChat.admin,
                              db.UserToChat.in_chat])
                    .select_from(db.User.join(db.UserToChat, db.UserToChat.user_id == db.User.user_id))
                    .where(and_(db.UserToChat.admin == 1, db.UserToChat.chat_id == m.chat_id))).gino.all()
    owner = await (db.select([db.User.user_id, db.User.names[1], db.User.nickname, db.UserToChat.in_chat])
                   .select_from(db.User.join(db.UserToChat, db.UserToChat.user_id == db.User.user_id))
                   .where(and_(db.UserToChat.admin == 2, db.UserToChat.chat_id == m.chat_id))).gino.first()
    users_id = [x[0] for x in admins]
    users = await evg.api.users.get(users_id, fields="online")
    if owner is not None:
        owner_id, owner_name, owner_nickname, in_chat = owner
        owner_online = (await evg.api.users.get(owner_id, fields="online"))[0].online
        reply += f"Создатель беседы:\n[id{owner_id}|{owner_name if owner_nickname is None else owner_nickname}] " \
                 f"{'🍵' if owner_online else '☕'}" \
                 f"{'🚪' if not in_chat else ''}\n\n"
    if len(users) == 1:
        await m.reply(reply)
        return
    reply += "Администраторы беседы:\n"
    i = 0
    for user_id, name, nickname, admin, status in admins:
        if admin == 1:
            reply += f"{i + 1}. [id{user_id}|{name if nickname is None else nickname}] " \
                     f"{'🍵' if users[i].online else '☕'}" \
                     f"{'🚪' if not status else ''}\n"
        i += 1
    await m.reply(reply)


@bot.on.chat_message(Command(["ранги", "все ранги", "rangs"]))
async def rangs_users_command(m: Message):
    ranks = await (db.select([db.User.user_id, db.User.names[1], db.User.nickname, db.UserToChat.rang])
                   .select_from(db.User.join(db.UserToChat, db.UserToChat.user_id == db.User.user_id))
                   .where(and_(db.UserToChat.rang > 0, db.UserToChat.in_chat.is_(True),
                               db.UserToChat.chat_id == m.chat_id))
                   .order_by(db.UserToChat.rang.desc())).gino.all()
    users_id = [x[0] for x in ranks]
    users_online = [x.online for x in await evg.api.users.get(users_id, fields="online")]
    reply = "📝 Список рангов беседы:\n"
    last_rang = 6
    i = 0
    for index, rang_data in enumerate(ranks):
        user_id, name, nickname, rang = rang_data
        if last_rang > rang:
            reply += "\n" + rangnames[rang] + ":\n"
            last_rang = rang
            i = 0
        reply += f"{i + 1}. [id{user_id}|{name if nickname is None else nickname}] " \
                 f"{'🍵' if users_online[index] else '☕'}\n"
        i += 1
    await m.reply(reply)


@bot.on.message(CommandWithAnyArgs("ник ", need_values=True, name_args="nickname"))
@bot.on.message(CommandWithAnyArgs("+ник ", need_values=True, name_args="nickname"))
@bot.on.message(CommandWithAnyArgs("ник: ", need_values=True, name_args="nickname"))
async def set_nickname_command(m: Message, nickname: str = None):
    is_vip_user = await db.select([db.User.ext_nick]).where(db.User.user_id == m.from_id).gino.scalar()
    if not is_vip_user and len(nickname) > 20:
        await m.reply("🚫 Обычным пользователям можно использовать в нике до 20 символов. Купите расширенный "
                              "ник, чтобы увеличить ограничение до 30. Команда «купить ник+»")
        return
    if is_vip_user and len(nickname) > 30:
        await m.reply("🚫 В нике можно использовать до 30 символов")
        return
    if not is_vip_user and not re.match(r"^[а-яА-ЯёЁa-zA-Z0-9.,!№@#$%^:&?*-_()\s]+$", nickname):
        await m.reply("🚫 В нике нельзя использовать запрещённые символы. Купите вип, чтобы "
                              "снять ограничение на символы. Команда «купить вип»")
        return
    await db.User.update.values(nickname=nickname).where(db.User.user_id == m.from_id).gino.status()
    await m.reply(f"✅ Ник успешно обновлён. теперь вы «{nickname}»")


@bot.on.chat_message(Command("убери ник"))
@bot.on.chat_message(Command("-ник"))
async def delete_nickname_command(m: Message):
    await db.User.update.values(nickname=None).where(db.User.user_id == m.from_id).gino.status()
    await m.reply("✅ Ник успешно убран")


@bot.on.chat_message(CommandWithAnyArgs("приветствие "), ChangeSettingsChat())
@bot.on.chat_message(CommandWithAnyArgs("приветствие: "), ChangeSettingsChat())
@bot.on.chat_message(CommandWithAnyArgs("+приветствие "), ChangeSettingsChat())
@bot.on.chat_message(CommandWithAnyArgs("+приветствие: "), ChangeSettingsChat())
async def set_hello(m: Message):
    hello_msg = m.text[17:]
    await db.Chat.update.values(hello_msg=hello_msg).where(db.Chat.chat_id == m.chat_id).gino.status()
    await m.reply("✅ Новое приветствие установлено!")


@bot.on.chat_message(Command("убери приветствие"), ChangeSettingsChat())
@bot.on.chat_message(Command("-приветствие"), ChangeSettingsChat())
async def del_hello(m: Message):
    await db.Chat.update.values(hello_msg=None).where(db.Chat.chat_id == m.chat_id).gino.status()
    await m.reply("✅ Приветствие успешно убрано!")


@bot.on.chat_message(CommandWithAnyArgs("прощание: "), ChangeSettingsChat())
@bot.on.chat_message(CommandWithAnyArgs("прощание "), ChangeSettingsChat())
@bot.on.chat_message(CommandWithAnyArgs("+прощание "), ChangeSettingsChat())
@bot.on.chat_message(CommandWithAnyArgs("+прощание: "), ChangeSettingsChat())
async def set_hello(m: Message):
    bye_msg = m.text[14:]
    await db.Chat.update.values(bye_msg=bye_msg).where(db.Chat.chat_id == m.chat_id).gino.status()
    await m.reply("✅ Новое прощание установлено!")


@bot.on.chat_message(Command("убери прощание"), ChangeSettingsChat())
@bot.on.chat_message(Command("-прощание"), ChangeSettingsChat())
async def del_hello(m: Message):
    await db.Chat.update.values(bye_msg=None).where(db.Chat.chat_id == m.chat_id).gino.status()
    await m.reply("✅ Прощание успешно убрано!")


@bot.on.chat_message(Command(["кто онлайн", "онлайн"]))
async def who_online(m: Message):
    users = await (db.select([db.User.user_id, db.User.names[1], db.User.nickname])
                   .select_from(db.User.join(db.UserToChat, db.UserToChat.user_id == db.User.user_id))
                   .where(and_(db.UserToChat.in_chat.is_(True), db.UserToChat.chat_id == m.chat_id))).gino.all()
    user_ids = [x[0] for x in users]
    users_ids_online = await evg.api.users.get(user_ids=user_ids, fields=["online"])
    reply = "📝 Список пользователей онлайн:\n\n"
    if len(users_ids_online) == 0:
        await m.reply("🚫 Никого онлайн нет")
        return
    users_info = [x for i, x in enumerate(users) if users_ids_online[i].online]
    for index, info in enumerate(users_info):
        user_id, user_name, user_nickname = info
        reply += f"{index + 1}. [id{user_id}|{user_name if user_nickname is None else user_nickname}]\n"
    await m.reply(reply)


@bot.on.message(InteractionUsers("гриб", False, False, True))
async def get_kombucha(m: Message, to_user_id: int):
    kombucha = await db.select([db.User.kombucha]).where(db.User.user_id == to_user_id).gino.scalar()
    if kombucha is None:
        await m.reply("🤷 Не знаю этого пользователя!")
        return
    kombucha = Decimal(kombucha).quantize(Decimal("1.000"))
    await m.reply(f"🍄 Рост гриба {await db.get_mention_user(to_user_id, 1)} составляет {kombucha} см")


@bot.on.message(InteractionUsers("рег", False, False, True))
async def get_registration_user(m: Message, to_user_id: int):
    register_date = await get_register_date(to_user_id)
    user = (await bot.api.users.get(to_user_id, name_case="gen"))[0]
    if register_date is None:
        await m.reply(f"📄 Дату регистрации [id{user.id}|{user.first_name} {user.last_name}] "
                              f"установить не удалось")
        return
    await m.reply(f"📄 Дата регистрации [id{user.id}|{user.first_name} {user.last_name}] "
                          f"{register_date.strftime(DATE_PARSING)}")


@bot.on.message(InteractionUsers("стикеры", False, False, True))
async def get_stickers(m: Message, to_user_id: int):
    stickers = await evg.api.request("store.getProducts",
                                        {"type": "stickers", "filters": "purchased", "user_id": to_user_id})
    sticker_ids = [x['id'] for x in stickers['response']['items']]
    st_info = await db.select([db.Sticker.name, db.Sticker.price]).where(db.Sticker.id.in_(sticker_ids)).gino.all()
    free_stickers = [x.name for x in st_info if x.price == 0]
    payment_stickers = [(x.name, x.price) for x in st_info if x.price > 0]
    user = await bot.api.users.get(to_user_id, name_case="gen")
    paiment = sum([x[1] for x in payment_stickers])
    async with aiofiles.open(f"Список стикерпаков {user[0].first_name} {user[0].last_name}.txt", mode="w", encoding="utf-8") as file:
        text = ', '.join(free_stickers)
        wrapped_text = '\n'.join(wrap(text, width=100))
        await file.write(f"Бесплатные стикерпаки:\n{wrapped_text}\n\n"
                   f"Платные стикерпаки:\n{', '.join([f'{x[0]}({x[1]})' for x in payment_stickers])}\n\n")
    attachment = await bot_doc_message_upl.upload(file_source=f"Список стикерпаков {user[0].first_name} {user[0].last_name}.txt",
                                                  title=f"Список стикерпаков {user[0].first_name} {user[0].last_name}.txt", peer_id=671385770)
    os.remove(f"Список стикерпаков {user[0].first_name} {user[0].last_name}.txt")
    await m.reply(f"😜 Информация по стикерам [id{user[0].id}|{user[0].first_name} {user[0].last_name}]\n\n"
                          f"Бесплатных стикерпаков: {len(free_stickers)} паков\n"
                          f"Платных стикерпаков: {len(payment_stickers)}\n"
                          f"Всего паков: {len(free_stickers)+len(payment_stickers)}\n"
                          f"Всего потрачено: {paiment} голосов <= {paiment * 7} руб.", attachment=attachment)


@bot.on.chat_message(InteractionUsers('какашка'))
async def shit_user(m: Message, to_user_id: int):
    await db.User.update.values(reaction=5).where(db.User.user_id == to_user_id).gino.status()
    await m.reply(f"Теперь я буду ставить какашку пользователю {await db.get_mention_user(to_user_id, 0)}")


@bot.on.chat_message(InteractionUsers('раскакашить'))
async def unshit_user(m: Message, to_user_id: int):
    await db.User.update.values(reaction=None).where(db.User.user_id == to_user_id).gino.status()
    await m.reply(f"Больше не буду ставить какашку на сообщения пользователя {await db.get_mention_user(to_user_id, 0)}")

