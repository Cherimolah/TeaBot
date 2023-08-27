from vkbottle.bot import Message
import re
from loader import bot
from typing import Union
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional
from db_api.db_engine import db
from utils.vkscripts import get_cases_users
from funcy import chunks

mention_regex = re.compile(r"\[(?P<type>id|club|public)(?P<id>\d*)\|(?P<text>.+)\]")
link_regex = re.compile(r"https:/(?P<type>/|/m.)vk.com/(?P<screen_name>\w*)")


# Функция для получения указание на пользователя из сообщения.
async def get_id_mention_from_message(m: Message, check_chat: bool = True, self_protect: bool = True,
                                      return_himself: bool = False) -> Union[bool, int]:
    # check_chat - нужна ли проверка наличия пользователя в чате
    # self_protect - вызывать ли ошибку если пользователь указал сам на себя
    # return_himself - вернуть самого пользователя, если никто не указан
    if m.reply_message is not None:
        user_id = m.reply_message.from_id
    elif m.fwd_messages:
        user_id = m.fwd_messages[0].from_id
    else:
        msg_text = m.text.lower().replace("\n", " ")
        match = re.search(mention_regex, msg_text)
        if match is not None:
            user_id = int(match.group("id")) if str(match.group("id")).isdigit() else 0
        else:
            match = re.search(link_regex, msg_text)
            if match is not None:
                screen_name = match.group("screen_name")
                user = await bot.api.utils.resolve_screen_name(screen_name)
                if user.object_id is None:
                    user_id = 0
                else:
                    user_id = user.object_id if user.type == user.type.USER else -user.object_id
            else:
                user_id = 0
    if user_id < 0:
        await bot.reply_msg(m, "🙅‍♂ Команда не работает с группами")
        return False
    if user_id == 0:
        if not return_himself:
            await bot.reply_msg(m, "🙅‍♂ Пользователь не указан")
            return False
        return m.from_id
    if self_protect and user_id == m.from_id:
        await bot.reply_msg(m, "🙄 Не будь таким самокритичным")
        return False
    if check_chat and not await db.is_user_in_chat(user_id, m.chat_id):
        print(user_id)
        await bot.reply_msg(m, "🤷 Этого пользователя нет в беседе")
        return False
    return user_id


async def get_register_date(user_id: int) -> Optional[datetime]:
    async with ClientSession() as session:
        response = await session.get(f"https://vk.com/foaf.php?id={user_id}")
        text = await response.text()
    soup = BeautifulSoup(text, "lxml")
    reg_dateime = soup.find("ya:created")
    if not reg_dateime:
        return
    reg_date_str, reg_time_str = reg_dateime.get("dc:date").split("T")
    year, month, day = list(map(int, reg_date_str.split("-")))
    hour, minute, second = list(map(int, reg_time_str.split("+")[0].split(":")))
    return datetime(year, month, day, hour, minute, second)


async def parse_user_cases(users_ids: list):
    "Получает пользователей со всеми падежами без лимита на 999 пользователей"
    users_ids_chunks = list(chunks(200, users_ids))  # Разбиваем по 999, т.к. вк за раз больше не принимает
    # Инфа о пользователях разбитая на чанки
    users_chunks_responses = [await get_cases_users(x) for x in users_ids_chunks]
    # Разворачиваем двумерный список обратно в одномерный
    users_responses = [x for y in users_chunks_responses for x in y]
    return users_responses
