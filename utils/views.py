from typing import List, Union, Tuple, Dict, Optional
import time
import asyncio
import random
import re

import grapheme

from db_api.db_engine import db, Punishments
from datetime import datetime
from utils.parsing import parse_unix_to_date
from vkbottle import VKAPIError
from vkbottle.bot import Message
from loader import bot, captcha_users
from sqlalchemy import and_
from vkbottle_types.responses.users import UsersUserFull
from utils.parsing_users import get_register_date
from markovify import NewlineText
from sqlalchemy import func
from openai import AsyncOpenAI

from config import GROUP_ID, ADMIN_ID, AI_API_KEY


ai_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=AI_API_KEY,
)


async def set_warn(chat_id: int, from_user_id: int, to_user_id: int, closing_at: int) -> None:
    await db.add_punishment(type_pun=Punishments.WARN, to_time=closing_at or None,
                            from_user_id=from_user_id, to_user_id=to_user_id, chat_id=chat_id)
    warns_count = await db.select([db.func.count(db.Punishment.id)]).where(and_(db.Punishment.type == 2,
                                                               db.Punishment.to_user_id == to_user_id)).gino.scalar()
    await bot.api.messages.send(
        message=f"⚠ {await db.get_mention_user(to_user_id, 0)}, вам выдано предупреждение "
                f"{parse_unix_to_date(closing_at)} "
                f"от {await db.get_mention_user(from_user_id, 1)}\n"
                f"Всего предупреждений {warns_count}/5",
        peer_id=2000000000 + chat_id, random_id=0, disable_mentions=True
    )
    if warns_count >= 5:
        admin = await (db.select([db.UserToChat.admin])
                       .where(and_(db.UserToChat.user_id == to_user_id, db.UserToChat.chat_id == chat_id))
                       ).gino.scalar()
        if admin > 0:
            await bot.api.messages.send(
                message=f"🚫 {await db.get_mention_user(to_user_id, 1)}, у вас достигнут лимит предупреждений, "
                        f"но я не могу вас исключить из-за настроек беседы",
                peer_id=2000000000 + chat_id, random_id=0, disable_mentions=True
            )
            return
        await bot.api.messages.send(
            message=f"🚫 {await db.get_mention_user(to_user_id, 1)}, вы были исключены из беседы "
                    f"за достижение лимита предупреждений", peer_id=2000000000 + chat_id, random_id=0,
            disable_mentions=True
        )
        try:
            await bot.api.messages.remove_chat_user(chat_id, member_id=to_user_id)
            await db.Punishment.delete.where(and_(db.Punishment.type == 1,
                                                  db.Punishment.chat_id == chat_id)).gino.status()
        except VKAPIError:
            pass


async def send_goodbye(chat_id: int, user_id: int):
    bye_msg = await db.select([db.Chat.bye_msg]).where(db.Chat.chat_id == chat_id).gino.scalar()
    if bye_msg:
        await bot.api.messages.send(chat_id + 2000000000, bye_msg)
        return
    await (db.UserToChat.update.values(in_chat=False)
           .where(and_(db.UserToChat.chat_id == chat_id, db.UserToChat.user_id == user_id))).gino.status()
    await bot.api.messages.send(chat_id + 2000000000, f"😢 Прощай, мы тебя никогда не забудем, "
                                             f"{await db.get_mention_user(user_id, 0)}")


async def wait_captcha_user(message: Message, user_id: int, time_sleep: int):
    await asyncio.sleep(time_sleep)
    await bot.api.messages.delete(peer_id=message.peer_id, cmids=[message.conversation_message_id],
                                  delete_for_all=True)
    if user_id in captcha_users:
        user = (await bot.api.users.get(user_id))[0]
        await bot.api.messages.send(message.peer_id, f'[id{user_id}|{user.first_name} {user.last_name}] был заблокирован так как не прошёл капчу')
        # message.chat_id атрибута нету, т.к. message там исходящий
        await db.UserToChat.update.values(in_chat=False).where(and_(db.UserToChat.chat_id == message.peer_id - 2000000000,
                                                                    db.UserToChat.user_id == user_id)).gino.status()
        await bot.api.messages.remove_chat_user(user_id=user_id, chat_id=message.peer_id - 2000000000)
        del captcha_users[user_id]
    else:
        hello_msg = await db.select([db.Chat.hello_msg]).where(db.Chat.chat_id == message.peer_id - 2000000000).gino.scalar()
        if hello_msg is None:
            await bot.api.messages.send(message.peer_id,
                                        f"✋ Приветсвую тебя, чаеман "
                                        f"{await db.get_mention_user(user_id, 0)}")
        else:
            await bot.api.messages.send(message.peer_id, hello_msg)


async def send_hello(chat_id: int, user_id: int, invited_by: int, send_message=True):
    if user_id < 0:
        return
    date_registration = await get_register_date(user_id)
    if date_registration:
        user = (await bot.api.users.get(user_id))[0]
        if (datetime.now() - date_registration).days < 3:
            admin = await db.select([db.UserToChat.user_id]).where(
                and_(db.UserToChat.admin == 2, db.UserToChat.chat_id == chat_id)
            ).gino.scalar()
            if not admin:
                admin = await db.select([db.UserToChat.user_id]).where(
                    and_(db.UserToChat.admin == 1, db.UserToChat.chat_id == chat_id)
                ).gino.scalar()
            if not admin:
                admin = await db.select([db.UserToChat.user_id]).where(
                    db.UserToChat.chat_id == chat_id
                ).gino.scalar()
            await bot.api.messages.send(chat_id + 2000000000,
                               f"📄 С момента регистрации пользователя "
                               f"[id{user.id}|{user.first_name} {user.last_name}] "
                               f"прошло менее 3 дней, наверняка это бот. Если ты человек можешь написать "
                               f"администратору {await db.get_mention_user(admin, 2)}")
            await bot.api.messages.remove_chat_user(chat_id, member_id=user_id)
            return
    res = await (db.select([db.User.user_id, db.User.names[2], db.User.nickname, db.Punishment.closing_at])
                 .select_from(db.User.join(db.Punishment, db.Punishment.from_user_id == db.User.user_id))
                 .where(and_(db.Punishment.to_user_id == user_id, db.Punishment.type == 3,
                             db.Punishment.chat_id == chat_id))
                 ).gino.first()
    if res:
        from_user_id, from_user_name, from_user_nickname, ban_time = res
        admin, rang = await db.select([db.UserToChat.admin, db.UserToChat.rang]).where(
            and_(db.UserToChat.user_id == invited_by, db.UserToChat.chat_id == chat_id)).gino.first()
        if admin <= 0 or rang < 2:
            await bot.api.messages.send(chat_id + 2000000000,
                               f"📝 У {await db.get_mention_user(user_id, 2)} есть бан до "
                               f"{parse_unix_to_date(ban_time)} от "
                               f"[id{from_user_id}|{from_user_name if from_user_nickname is None else from_user_nickname}].\n"
                               )
            await bot.api.messages.remove_chat_user(chat_id, member_id=user_id)
            return
        else:
            await db.Punishment.delete.where(and_(db.Punishment.type == 3, db.Punishment.to_user_id == user_id,
                                                  db.Punishment.chat_id == chat_id)).gino.status()
            await bot.api.messages.send(
                chat_id + 2000000000,
                f"📝 У {await db.get_mention_user(user_id, 2)} есть бан до "
                f"{parse_unix_to_date(ban_time)} от "
                f"[id{from_user_id}|{from_user_name if from_user_nickname is None else from_user_nickname}].\n"
                f"Но {'её' if await db.is_woman_user(chat_id + 2000000000) else 'его'} пригласил адсинистратор. "
                f"Снимаю бан автоматически"
            )
    if not await db.select([db.UserToChat.user_id]).where(
            and_(db.UserToChat.user_id == user_id, db.UserToChat.chat_id == chat_id)).gino.scalar():
        await db.UserToChat.create(user_id=user_id, invited_by=invited_by, chat_id=chat_id, joined_at=datetime.now())
        is_group = await db.select([db.Chat.is_group]).where(db.Chat.chat_id == chat_id).gino.scalar()
        if is_group:
            a = random.randint(1, 9)
            b = random.randint(1, 9)
            answer = a + b
            captcha_users[user_id] = answer
            message = (await bot.api.messages.send(peer_id=2000000000 + chat_id,
                                                   message=f"Привет, {await db.get_mention_user(user_id, 0)}\n\n"
                                                           f"Докажи, что ты не бот, реши пример: {a} + {b}\n\n"
                                                           f"На решение даётся 20 секунд!"))[0]
            asyncio.get_event_loop().create_task(
                wait_captcha_user(message, user_id, 20)
            )
            return
    else:
        await db.UserToChat.update.values(in_chat=True).where(and_(db.UserToChat.user_id == user_id,
                                                                   db.UserToChat.chat_id == chat_id)).gino.status()
    if send_message:
        hello_msg = await db.select([db.Chat.hello_msg]).where(db.Chat.chat_id == chat_id).gino.scalar()
        if hello_msg is None:
            await bot.api.messages.send(chat_id + 2000000000,
                               f"✋ Приветсвую тебя, чаеман "
                               f"{await db.get_mention_user(user_id, 0)}")
        else:
            await bot.api.messages.send(chat_id + 2000000000, hello_msg)


def get_names_user(index: int, user_cases: List[UsersUserFull]) -> list:
    user = user_cases[index]
    return [
        f"{user.first_name_nom} {user.last_name_nom}",
        f"{user.first_name_gen} {user.last_name_gen}",
        f"{user.first_name_dat} {user.last_name_dat}",
        f"{user.first_name_acc} {user.last_name_acc}",
        f"{user.first_name_ins} {user.last_name_ins}",
        f"{user.first_name_abl} {user.last_name_abl}"
    ]


async def waiting_punishment(punishment_id: int, to_time: Union[int, datetime]):
    if isinstance(to_time, datetime):
        to_time = time.mktime(to_time.timetuple())
    await asyncio.sleep(to_time - time.time())
    exist = await db.select([db.Punishment.id]).where(db.Punishment.id == punishment_id).gino.scalar()
    if exist:
        pun_id, pun_type, chat_id, created_at, closing_at, from_user_id, to_user_id = await (db.select([*db.Punishment])
            .where(db.Punishment.id == punishment_id)).gino.first()
        if await bot.api.messages.is_messages_from_group_allowed(GROUP_ID, to_user_id):
            await db.Punishment.delete.where(db.Punishment.id == pun_id).gino.status()
            if pun_type == Punishments.MUTE.value:
                await bot.api.request('messages.changeConversationMemberRestrictions',
                                      {'peer_id': chat_id + 2000000000, 'member_ids': to_user_id, 'action': 'rw'})
            await bot.api.messages.send(to_user_id,
                               f"🎉🎊 {await db.get_mention_user(to_user_id, 0)}, у вас закончился срок "
                               f"{'бана' if pun_type == 3 else 'варна' if pun_type == 2 else 'мута'}, выданного "
                               f"в беседе {(await bot.api.messages.get_conversations_by_id(chat_id + 2000000000)).items[0].chat_settings.title} "
                               f"выданный пользователем {await db.get_mention_user(from_user_id, 1)} в "
                               f"{parse_unix_to_date(created_at)}")


async def remember_kombucha(user_id: int, delay: float):
    await asyncio.sleep(delay)
    if (await bot.api.messages.is_messages_from_group_allowed(GROUP_ID, user_id)).is_allowed:
        await bot.api.messages.send(user_id, "⏰ Твой гриб доступен для рандома!")


async def generate_text(max_chars: int = 4096) -> str:
    history = [x[0] for x in await db.select([db.Message.text]).order_by(func.random()).limit(5000).gino.all()]
    text_model = NewlineText(input_text="\n".join(history), state_size=1, well_formed=False)
    return text_model.make_short_sentence(
        max_chars=max_chars, tries=100
    ) or "Сгенерировать текст не удалось"


async def refill_balance(payment: db.Payment):
    await db.Payment.update.values(is_claimed=True).where(db.Payment.id == payment.id).gino.status()
    await bot.api.messages.edit(peer_id=payment.peer_id, cmid=payment.cmid, message="🎉 Баланс успешно пополнен")
    await db.User.update.values(balance=db.User.balance+payment.amount).where(db.User.user_id == payment.user_id).gino.status()
    await bot.api.messages.send(message=f'🎉 Пополнен баланс на сумму {payment.amount}🧊!', peer_id=payment.user_id, random_id=0)
    await bot.api.messages.send(message=f'{await db.get_mention_user(payment.user_id, 0)} пополнил баланс на {payment.amount} рублей',
                                peer_id=ADMIN_ID, random_id=0)


async def generate_ai_text(messages) -> Tuple[str, Optional[Dict]]:
    completion = await ai_client.chat.completions.create(
        model="google/gemini-2.0-pro-exp-02-05:free",
        messages=messages
    )
    if not completion.choices:
        return 'Не удалось сгенерировать ответ', None
    text = completion.choices[0].message.content.replace('</think>', '')
    text = text.replace('\\n', '\n')
    if not text:
        return 'Не удалось сгенерировать ответ', None
    text = re.sub(r'\n{3,}', '\n\n', text)
    return format_text(text)


def remove_variation_selectors(text):
    text = text.replace("\ufe0f", "")
    return text


def format_text(text: str) -> Tuple[str, Optional[Dict]]:
    text = remove_variation_selectors(text)
    print(text)
    clean_text = text.replace('`', '').replace('**', '')
    markdown = False
    a = text.replace('```', '').replace('`', '')
    a = re.sub(r'\n{3,}', '\n\n', a)
    bold_pattern = re.finditer(r'\*\*(.*?)\*\*', a, re.DOTALL)

    offsets = []

    shift = 0
    for match in bold_pattern:
        markdown = True
        start, end = match.span()
        offsets.append({"type": "bold", "offset": grapheme.length(clean_text[:start - shift]), 'length': end - start - 4})
        shift += 4

    b = text.replace("**", '').replace('```', '')
    b = re.sub(r'\n{3,}', '\n\n', b)
    italic_pattern = re.finditer(r'`(.*?)`', b, re.DOTALL)

    shift = 0
    for match in italic_pattern:
        markdown = True
        start, end = match.span()
        offsets.append({"type": "italic", "offset": grapheme.length(clean_text[:start - shift]), 'length': end - start - 2})
        shift += 2

    c = text.replace('**', '')
    c = re.sub(r'(?<!`)`(?!`)', '', c)

    italic_pattern = re.finditer(r'```(.*?)```', c, re.DOTALL)

    shift = 0
    for match in italic_pattern:
        markdown = True
        start, end = match.span()
        offsets.append({"type": "italic", "offset": grapheme.length(clean_text[:start - shift]), 'length': end - start - 6})
        shift += 8

    if markdown:
        format_data = {
            "version": 1,
            "items": offsets
        }
        return clean_text, format_data
    else:
        return clean_text, None
