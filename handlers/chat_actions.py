from loader import bot
from vkbottle.bot import Message, MessageEvent
from vkbottle.dispatch.rules.base import PayloadMapRule
from config import ADMIN_ID
from db_api.db_engine import db
from vkbottle import VKAPIError
from keyboards import generators
from vkbottle import GroupEventType
from config import rangnames
from utils.views import send_goodbye, send_hello
from sqlalchemy import and_
from utils.custom_rules import GroupInvited, UserInvited, UserLeft, UserKicked


@bot.on.chat_message(GroupInvited())
async def group_invited(m: Message):
    await bot.write_msg(m.peer_id, "🙋‍♂ Приветствую. Для полноценного использования бота нужно выдать мне права "
                                  "администратора и написать любое сообщение. Полный список команд: "
                                  "https://vk.com/@your_tea_bot-help",
                       attachment="photo-201071106_457240238_dd33c83bbd28a8545e")
    await bot.write_msg(ADMIN_ID, f"Бот добавлен в беседу {m.chat_id}")


@bot.on.chat_message(UserInvited())
async def user_invited(m: Message):
    await send_hello(m.chat_id, m.action.member_id, m.from_id)


@bot.on.chat_message(UserKicked())
async def user_kicked_command(m: Message):
    await send_goodbye(m.chat_id, m.action.member_id)


@bot.on.chat_message(UserLeft())
async def user_lived_command(m: Message):
    await user_kicked_command(m)
    kb = generators.user_left_kb(m.action.member_id)
    await bot.write_msg(m.peer_id, f"{await db.get_mention_user(m.action.member_id, 0)} Вышел из беседы. Кикнуть?",
                       keyboard=kb)


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, PayloadMapRule({"kick_user": int}))
async def kick_user_button(m: MessageEvent):
    user_id = m.payload['kick_user']
    rang, admin = await db.select([db.UserToChat.rang, db.UserToChat.admin]).where(
        and_(db.UserToChat.user_id == m.user_id, db.UserToChat.chat_id == m.peer_id - 2000000000)
    ).gino.first()
    if rang < 3 or admin < 1:
        await bot.send_ans(m, f"⛔ Исключать пользователей можно с ранга {rangnames[3]}")
        return
    if not await db.is_higher(m.peer_id-2000000000, m.user_id, user_id):
        await bot.send_ans(m, "🙅‍♂ Пользователь выше или одинакового с вами ранга")
        return
    try:
        await bot.api.messages.remove_chat_user(m.peer_id-2000000000, member_id=user_id)
        await db.UserToChat.update.values(in_chat=False).where(
            and_(db.UserToChat.user_id == user_id, db.UserToChat.chat_id == m.peer_id-2000000000)
        ).gino.status()
        await bot.change_msg(m, f"⚠ {await db.get_mention_user(user_id, 0)} исключён")
    except VKAPIError:
        await bot.change_msg(m, f"Не могу исключить {await db.get_mention_user(user_id, 3)}")
