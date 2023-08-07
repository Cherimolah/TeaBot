from loader import bot
from vkbottle import BaseStateGroup
from db_api.db_engine import db
import asyncio
from vkbottle.bot import Message
import re
from utils.parsing_users import get_id_mention_from_message
from sqlalchemy import and_
import random
from typing import List, Dict
from emoji import EMOJI_DATA
from utils.photos import re_upload_photo
from utils.custom_rules import RPCommandRule, OwnerRPCommand

mention_regex = re.compile(r"\[(?P<type>id|club|public)(?P<id>\d*)\|(?P<text>.+)\]")
link_regex = re.compile(r"https:/(?P<type>/|/m.)vk.com/(?P<screen_name>\w*)")


class AddingRPCommand(BaseStateGroup):

    COMMAND = "command"
    EMOJI = "emoji"
    ACTION = "action"
    NAME_CASE = "name_case"
    PHOTOS = "photos"


class RPCommand:

    command: str
    emoji: str
    action: str
    name_case: int
    photos: List[str]


context: Dict[int, RPCommand] = {}


async def role_play_command(m: Message, command: str = None, owner: int = None):
    to_user_id = await get_id_mention_from_message(m, self_protect=False, check_chat=True)
    if not to_user_id:
        return
    if not await db.is_woman_user(m.from_id):
        emoji, action, specify, name_case, photos = await (db.select([
            db.RPCommand.emoji, db.RPCommand.action, db.RPCommand.specify, db.RPCommand.name_case, db.RPCommand.photos])
                                                           .where(and_(db.RPCommand.command == command,
                                                                       db.RPCommand.owner == owner))).gino.first()
    else:
        emoji, action, specify, name_case, photos = await (db.select([
            db.RPCommand.emoji, db.RPCommand.wom_action, db.RPCommand.specify, db.RPCommand.name_case,
            db.RPCommand.photos])
                                                           .where(and_(db.RPCommand.command == command,
                                                                       db.RPCommand.owner == owner))).gino.first()
    user_name = await db.get_mention_user(m.from_id, 0)
    to_user_name = await db.get_mention_user(to_user_id, name_case - 1)
    replic = m.text.replace("\n", " ")[len(command) + 1:].lstrip()
    match = re.search(mention_regex, replic)
    if match is not None:
        replic = replic[match.span()[1]:].lstrip()
    else:
        match = re.search(link_regex, replic)
        if match is not None:
            replic = replic[match.span()[1]:].lstrip()
    photo = random.choice(photos) if photos else None
    await bot.reply_msg(m, f"{emoji} {user_name} {action} {specify if specify is not None else ''} "
                          f"{to_user_name}\n"
                          f"{f'💬 С репликой: «{replic}»' if replic != '' else ''}", attachment=photo)


@bot.on.chat_message(text=["обнять всех"])
async def hug_all(m: Message):
    await bot.reply_msg(m, f"🤗 {await db.get_mention_user(m.from_id, 0)} обнял сразу всех")


@bot.on.private_message(text="+рп")
async def add_rp_command(m: Message):
    balance = await db.select([db.User.balance]).where(db.User.user_id == m.from_id).gino.scalar()
    if balance < 5:
        await bot.reply_msg(m, "Создание собственной рп команды стоит 5 🧊. Напиши «пополнить баланс {сумма}»\n"
                              "✅ Ты сможешь использовать их в любых чатах")
        return
    command = RPCommand()
    context[m.peer_id] = command
    await bot.state_dispenser.set(m.peer_id, AddingRPCommand.COMMAND)
    await db.User.update.values(balance=db.User.balance-5).where(db.User.user_id == m.from_id).gino.status()
    await bot.reply_msg(m, "Напиши текст по которой будет вызываться команда. Например: сжечь")


@bot.on.private_message(state=AddingRPCommand.COMMAND)
async def set_command(m: Message):
    command_id = await db.select([db.RPCommand.id]).where(
        and_(db.RPCommand.command == m.text.lower(), db.RPCommand.owner.is_(None))).gino.scalar()
    if command_id:
        await bot.reply_msg(m, "Это общедоступная команда, придумай себе другую")
        return
    command_id = await db.select([db.RPCommand.id]).where(
        and_(db.RPCommand.command == m.text.lower(), db.RPCommand.owner == m.from_id)).gino.scalar()
    if command_id:
        await bot.reply_msg(m, "У тебя уже есть такая команда")
        return
    if len(m.text) > 20:
        await bot.reply_msg(m, "Зачем тебе такая большая команда? Сократи до 20 символов")
    context[m.peer_id].command = m.text.lower()
    await bot.state_dispenser.set(m.peer_id, AddingRPCommand.EMOJI)
    await bot.reply_msg(m, "Пришли одно или два эмодзи, которые будут использоваться. Например: 🔥")


@bot.on.private_message(state=AddingRPCommand.EMOJI)
async def set_emoji(m: Message):
    if len(m.text) > 2:
        await bot.reply_msg(m, "Давай ограничимся двумя эмодзи")
        return
    for em in m.text:
        if em not in EMOJI_DATA:
            await bot.reply_msg(m, "У тебя что-то не из эмодзи")
            return
    context[m.peer_id].emoji = m.text
    await bot.state_dispenser.set(m.peer_id, AddingRPCommand.ACTION)
    await bot.reply_msg(m, "Теперь напиши действие рп-команды. "
                          "Можно использовать несколько слов. Например: сжёг на костре")


@bot.on.private_message(state=AddingRPCommand.ACTION)
async def set_action(m: Message):
    context[m.peer_id].action = m.text
    await bot.state_dispenser.set(m.peer_id, AddingRPCommand.NAME_CASE)
    await bot.reply_msg(m, "Теперь выбери падеж, который будет использоваться\n\n"
                          "1. Именительный (Евгений)\n"
                          "2. Родительный (Евгения)\n"
                          "3. Дательный (Евгению)\n"
                          "4. Винительный (Евгения)\n"
                          "5. Творительный (Евгением)\n"
                          "6. Предложный (Евгением)")


@bot.on.private_message(state=AddingRPCommand.NAME_CASE)
async def set_name_case(m: Message):
    try:
        name_case = int(m.text)
    except TypeError:
        await bot.reply_msg(m, "Отправь одно число от 1 до 6")
        return
    if name_case not in list(range(1, 6)):
        await bot.reply_msg(m, "Нужно числот от 1 до 6")
        return
    context[m.peer_id].name_case = name_case
    await bot.state_dispenser.set(m.peer_id, AddingRPCommand.PHOTOS)
    await bot.reply_msg(m, "Отправляй фотографии, которые будут использоваться для твоей рп-команды")


@bot.on.private_message(state=AddingRPCommand.PHOTOS)
async def set_photos(m: Message):
    m_full = (await bot.api.messages.get_by_id([m.id])).items[0]
    photos = [x.photo for x in m_full.attachments if x.type == x.type.PHOTO]
    context[m.peer_id].photos = []
    message = (await bot.reply_msg(m, f"Загружаю фотографии 0/{len(photos)}"))[0]
    for i, photo in enumerate(photos):
        string = await re_upload_photo(photo, f"role_play{m.from_id}.jpg")
        context[m.peer_id].photos.append(string)
        await bot.edit_msg(message, f"Загружаю фотографии {i+1}/{len(photos)}")
    command = context[m.peer_id]
    await db.RPCommand.create(command=command.command, emoji=command.emoji, action=command.action,
                              name_case=command.name_case, wom_action=command.action, photos=command.photos,
                              owner=m.from_id)

    @bot.on.chat_message(RPCommandRule(command.command), OwnerRPCommand(m.from_id))
    async def send_user_rp_command(m1: Message):
        await role_play_command(m1, command.command, m.from_id)

    del context[m.peer_id]
    await bot.state_dispenser.delete(m.peer_id)
    await bot.edit_msg(message, "Рп команда добавлена! Теперь ты можешь использовать её в любой беседе со мной")


async def add_rp_commands():
    commands = [(x.command, x.owner) for x in await (db.select([db.RPCommand.command, db.RPCommand.owner])
                                                     .order_by(db.RPCommand.id.asc())).gino.all()]
    for com, user_id in commands:
        @bot.on.chat_message(RPCommandRule(com), OwnerRPCommand(user_id))
        async def role_play_handler(m: Message, command: str = None, owner: int = None):
            await role_play_command(m, command, owner)


asyncio.get_event_loop().run_until_complete(add_rp_commands())
