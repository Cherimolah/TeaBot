from db.chat_database import ChatDB
from vkbottle.bot import Message
import re


mention_regex = re.compile(r"\[(?P<type>id|club|public)(?P<id>\d*)\|(?P<text>.+)\]")
link_regex = re.compile(r"https:/(?P<type>/|/m.)vk.com/(?P<screen_name>\w*)")


# Функция для получения указание на пользователя из сообщения.
# Возвращает 0, если никто не указан, -1 если пользователь отсутствует в беседе
async def get_id_mention_from_message(m: Message) -> int:
    chat_db = await ChatDB().connect(m.chat_id)
    if m.reply_message is not None:
        await chat_db.sql.execute("SELECT id FROM users WHERE id = ?", (m.reply_message.from_id,))
        res = await chat_db.sql.fetchone()
        return m.reply_message.from_id if res is not None else -1
    if m.fwd_messages:
        await chat_db.sql.execute("SELECT id FROM users WHERE id = ?", (m.fwd_messages[0].from_id,))
        res = await chat_db.sql.fetchone()
        return m.fwd_messages[0].from_id if res is not None else -1
    msg_text = m.text.lower().replace("\n", " ")
    match = re.search(mention_regex, msg_text)
    if match is not None:
        return int(match.group("id")) if str(match.group("id")).isdigit() else 0
    match = re.search(link_regex, msg_text)
    if match is not None:
        screen_name = match.group("screen_name")
    else:
        return 0
    await chat_db.sql.execute("SELECT id FROM users WHERE screen_name = ?", (screen_name,))
    user_id = await chat_db.sql.fetchone()
    await chat_db.db.close()
    return user_id[0] if user_id is not None else -1
