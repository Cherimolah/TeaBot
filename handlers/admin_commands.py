from loader import bot
from vkbottle.bot import Message
from utils.parsing import parse_unix_to_date
from vkbottle import VKAPIError
from config import rangnames
from utils.custom_rules import AdminCommand
from db_api.db_engine import db, Punishments
from utils.views import set_warn
from sqlalchemy import and_


@bot.on.message(AdminCommand("бан", 3, True))
async def ban_command(m: Message, to_user_id: int = None, to_time: int = None):
    res = await (db.select([db.User.user_id, db.User.names[2], db.User.nickname, db.Punishment.closing_at])
                 .select_from(db.User.join(db.Punishment, db.Punishment.from_user_id == db.User.user_id))
                 .where(and_(db.Punishment.type == 3, db.Punishment.to_user_id == to_user_id,
                             db.Punishment.chat_id == m.chat_id))).gino.first()
    if res is not None:
        from_user_id, from_user_name, from_user_nickname, ban_time = res
        await m.reply(f"📝 У {await db.get_mention_user(to_user_id, 1)} уже есть бан до "
            f"{parse_unix_to_date(ban_time)} от "
            f"[id{from_user_id}|{from_user_name if from_user_nickname is None else from_user_nickname}]"
        )
        return
    to_user_admin = await db.is_admin_user(to_user_id, m.chat_id)
    if to_user_admin:
        await m.reply("🙅‍♂ Не могу исключить пользователя настройками вк")
        return
    await db.add_punishment(Punishments.BAN, to_time, m.chat_id, m.from_id, to_user_id)
    from_user_name = await db.get_mention_user(m.from_id, 4)
    to_user_name = await db.get_mention_user(to_user_id, 0)
    await m.reply(f"⛔ {to_user_name} обвиняется {from_user_name} в незаконной любви к кофе. Вам запрещено "
                          f"появляться в этой беседе до {parse_unix_to_date(to_time)}")
    try:
        await bot.api.messages.remove_chat_user(m.chat_id, member_id=to_user_id)
    except VKAPIError:
        pass


@bot.on.chat_message(AdminCommand("анбан", 3, check_chat=False))
@bot.on.chat_message(AdminCommand("разбан", 3, check_chat=False))
async def unban_command(m: Message, to_user_id: int = None):
    res = await (db.select([db.User.user_id, db.User.names[2], db.User.nickname, db.Punishment.id])
                 .select_from(db.User.join(db.Punishment, db.Punishment.to_user_id == db.User.user_id))
                 .where(and_(db.Punishment.to_user_id == to_user_id, db.Punishment.type == 3,
                             db.Punishment.chat_id == m.chat_id))).gino.first()
    if res is None:
        await m.reply(f"📝 У {await db.get_mention_user(to_user_id, 1)} нет бана")
        return
    to_user_id, to_user_name, to_user_nickname, ban_id = res
    await db.Punishment.delete.where(and_(db.Punishment.type == 3, db.Punishment.chat_id == m.chat_id,
                                          db.Punishment.to_user_id == to_user_id)).gino.status()
    await m.reply(f"✅ {await db.get_mention_user(m.from_id, 0)} снял{'а' if await db.is_woman_user(m.from_id) else ''} бан с "
           f"[id{to_user_id}|{to_user_name if to_user_nickname is None else to_user_nickname}]")


@bot.on.chat_message(AdminCommand("мут", 1, True))
async def mute_command(m: Message, to_user_id: int = None, to_time: int = None):
    res = await (db.select([db.User.user_id, db.User.names[2], db.User.nickname, db.Punishment.closing_at])
                 .select_from(db.User.join(db.Punishment, db.Punishment.from_user_id == db.User.user_id))
                 .where(and_(db.Punishment.type == 1, db.Punishment.to_user_id == to_user_id,
                             db.Punishment.chat_id == m.chat_id))).gino.first()
    if res is not None:
        from_user_id, from_user_name, from_user_nickname, mute_time = res
        await m.reply(
                           f"📝 У {await db.get_mention_user(to_user_id, 1)} уже есть мут от "
                           f"[id{from_user_id}|{from_user_name if from_user_nickname is None else from_user_nickname}]"
                           f" до {parse_unix_to_date(mute_time)}")
        return
    await db.add_punishment(Punishments.MUTE, to_time, m.chat_id, m.from_id, to_user_id)
    await bot.api.request('messages.changeConversationMemberRestrictions',
                          {'peer_id': m.peer_id, 'member_ids': to_user_id, 'action': 'ro'})
    await m.reply(f"🤐 {await db.get_mention_user(m.from_id, 0)} выдал мут "
                          f"{await db.get_mention_user(to_user_id, 2)} до {parse_unix_to_date(to_time)}")


@bot.on.chat_message(AdminCommand("размут", 1))
@bot.on.chat_message(AdminCommand("анмут", 1))
async def clear_mute_command(m: Message, to_user_id: int):
    res = await (db.select([db.User.user_id, db.User.names[2], db.User.nickname, db.Punishment.id])
                 .select_from(db.User.join(db.Punishment, db.Punishment.to_user_id == db.User.user_id))
                 .where(and_(db.Punishment.to_user_id == to_user_id, db.Punishment.type == 1,
                             db.Punishment.chat_id == m.chat_id))).gino.first()
    if res is None:
        await m.reply(f"📝 У {await db.get_mention_user(to_user_id, 1)} нет мута")
        return
    to_user_id, to_user_name, to_user_nickname, ban_id = res
    await db.Punishment.delete.where(and_(db.Punishment.type == 1, db.Punishment.chat_id == m.chat_id,
                                          db.Punishment.to_user_id == to_user_id)).gino.status()
    await bot.api.request('messages.changeConversationMemberRestrictions',
                          {'peer_id': m.peer_id, 'member_ids': to_user_id, 'action': 'rw'})
    await m.reply(f"✅ {await db.get_mention_user(m.from_id, 0)} снял{'а' if await db.is_woman_user(to_user_id) else ''} мут с "
           f"[id{to_user_id}|{to_user_name if to_user_nickname is None else to_user_nickname}]")


@bot.on.chat_message(AdminCommand("варн", 2, True))
async def warn_command(m: Message, to_user_id: int, to_time: int):
    await set_warn(m.chat_id, m.from_id, to_user_id, to_time)


@bot.on.chat_message(AdminCommand("анварн", 2))
async def un_warn_command(m: Message, to_user_id: int):
    res = await (db.select([db.User.user_id, db.User.names[2], db.User.nickname, db.Punishment.id])
                 .select_from(db.User.join(db.Punishment, db.Punishment.to_user_id == db.User.user_id))
                 .where(and_(db.Punishment.to_user_id == to_user_id, db.Punishment.chat_id == m.chat_id))
                 .gino.first())
    if not res:
        await m.reply(f"📝 У {await db.get_mention_user(to_user_id, 1)} нет предупреждений")
        return
    to_user_id, to_user_name, to_user_nickname, ban_id = res
    await db.Punishment.delete.where(and_(db.Punishment.type == 2, db.Punishment.to_user_id == to_user_id,
                                          db.Punishment.chat_id == m.chat_id)).gino.status()
    await m.reply(f"✅ {await db.get_mention_user(m.from_id, 0)} снял{'а' if await db.is_woman_user(to_user_id) else ''} "
           f"все предупреждения с [id{to_user_id}|{to_user_name if to_user_nickname is None else to_user_nickname}]")


@bot.on.chat_message(AdminCommand("кик", 2))
async def un_warn_command(m: Message, to_user_id: int):
    if await db.is_admin_user(to_user_id, m.chat_id):
        await m.reply("🙅‍♂ Не могу исключить пользователя настройками вк")
        return
    if await db.select([db.UserToChat.in_chat]).where(
            and_(db.UserToChat.chat_id == m.chat_id, db.UserToChat.user_id == to_user_id)).gino.scalar():
        await m.reply(f"🕵 {await db.get_mention_user(to_user_id, 0)} подозревается "
                              f"{await db.get_mention_user(m.from_id, 4)} в любви к кофе. "
                              f"Исключаем до выяснения обстоятельств")
        try:
            await bot.api.messages.remove_chat_user(m.chat_id, member_id=to_user_id)
        except VKAPIError:
            pass
    else:
        await m.reply(f"🙅‍♂ {await db.get_mention_user(to_user_id, 0)} уже исключён")


@bot.on.chat_message(AdminCommand("повысить", 0))
async def increase_user_command(m: Message, to_user_id: int):
    rang = await db.select([db.UserToChat.rang]).where(
        and_(db.UserToChat.user_id == to_user_id, db.UserToChat.chat_id == m.chat_id)
    ).gino.scalar()
    if rang >= 5:
        await m.reply(f"🚫 У {await db.get_mention_user(to_user_id, 1)} уже максимальный ранг")
        return
    await db.UserToChat.update.values(rang=db.UserToChat.rang + 1).where(
        and_(db.UserToChat.user_id == to_user_id, db.UserToChat.chat_id == m.chat_id)
    ).gino.status()
    await m.reply(f"✅ {await db.get_mention_user(m.from_id, 0)} повысил "
                          f"{await db.get_mention_user(to_user_id, 3)}. Теперь у "
                          f"{await db.get_mention_user(to_user_id, 1)} ранг {rangnames[rang + 1]}")


@bot.on.chat_message(AdminCommand("понизить", 0))
async def decrease_user_command(m: Message, to_user_id: int):
    rang = await db.select([db.UserToChat.rang]).where(
        and_(db.UserToChat.user_id == to_user_id, db.UserToChat.chat_id == m.chat_id)
    ).gino.scalar()
    if rang <= 0:
        await m.reply(f"🚫 У {await db.get_mention_user(to_user_id, 1)} уже минимальный ранг")
        return
    await db.UserToChat.update.values(rang=db.UserToChat.rang - 1).where(
        and_(db.UserToChat.user_id == to_user_id, db.UserToChat.chat_id == m.chat_id)
    ).gino.status()
    await m.reply(f"✅ {await db.get_mention_user(m.from_id, 0)} понизил "
                          f"{await db.get_mention_user(to_user_id, 3)}. Теперь у "
                          f"{await db.get_mention_user(to_user_id, 1)} ранг {rangnames[rang - 1]}")


@bot.on.chat_message(AdminCommand("ранг", 0))
async def set_rang(m: Message, to_user_id: int):
    try:
        rank = int(m.text.split(" ")[-1])
    except ValueError:
        await m.reply("🚫 В конце укажите номер ранга")
        return
    if not 0 <= rank <= 5:
        await m.reply("🚫 Укажите ранг от 0 до 5 включительно")
        return
    await db.UserToChat.update.values(rang=rank).where(
        and_(db.UserToChat.user_id == to_user_id, db.UserToChat.chat_id == m.chat_id)
    ).gino.status()
    await m.reply(f"✅ {await db.get_mention_user(m.from_id, 0)} установил "
                          f"{await db.get_mention_user(to_user_id, 2)} ранг {rangnames[rank]}")


@bot.on.chat_message(AdminCommand("тихийрежим", 2, for_all=True))
@bot.on.chat_message(AdminCommand("тихий режим", 2, for_all=True))
async def silent_mode(m: Message):
    if not await db.select([db.Chat.silent_mode]).where(db.Chat.chat_id == m.chat_id).gino.scalar():
        await bot.api.request('messages.disableChatWriting', {"chat_id": m.chat_id})
        await db.Chat.update.values(silent_mode=True).where(db.Chat.chat_id == m.chat_id).gino.status()
        await m.reply('Теперь писать в чат могут только администраторы')
    else:
        await bot.api.request('messages.enableChatWriting', {"chat_id": m.chat_id})
        await db.Chat.update.values(silent_mode=False).where(db.Chat.chat_id == m.chat_id).gino.status()
        await m.reply('Теперь писать в чат могут все участники')


@bot.on.chat_message(AdminCommand('выключить генерацию', 2, for_all=True))
@bot.on.chat_message(AdminCommand('выкл ген', 2, for_all=True))
@bot.on.chat_message(AdminCommand('disable generation', 2, for_all=True))
@bot.on.chat_message(AdminCommand('dis gen', 2, for_all=True))
async def disable_generation(m: Message):
    await db.Chat.update.values(generation_mode=False).where(db.Chat.chat_id == m.chat_id).gino.status()
    await m.reply('🚫🤖🧠 Генерация случайного текста отключена')


@bot.on.chat_message(AdminCommand('включить генерацию', 2, for_all=True))
@bot.on.chat_message(AdminCommand('вкл ген', 2, for_all=True))
@bot.on.chat_message(AdminCommand('enable generation', 2, for_all=True))
@bot.on.chat_message(AdminCommand('en gen', 2, for_all=True))
async def disable_generation(m: Message):
    await db.Chat.update.values(generation_mode=True).where(db.Chat.chat_id == m.chat_id).gino.status()
    await m.reply('✅🤖🧠 Генерация случайного текста включена')
