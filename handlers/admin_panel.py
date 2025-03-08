import json
import os

from loader import bot
from vkbottle.bot import Message
from config import ADMIN_ID
from db_api.db_engine import db
from vkbottle_types.objects import MessagesMessageAttachmentType

from utils.photos import download_photo
from bots.uploaders import bot_photo_message_upl
from utils.custom_rules import AdminPanelCommand
from utils.photos import re_upload_photo


@bot.on.private_message(AdminPanelCommand("скл "))
async def sql_injection(m: Message):
    sql_script = m.text[4:]
    result = await db.all(sql_script)
    await bot.api.messages.send(ADMIN_ID, message=f"Результат выполнения скрипта:", random_id=0)
    for i in range(0, len(str(result)), 4096):
        await bot.api.messages.send(ADMIN_ID, message=str(result)[i:i+4096], random_id=0)


@bot.on.private_message(AdminPanelCommand("аттач бот"))
async def get_attachment_string(m: Message):
    message = await m.get_full_message()
    string_at = ""
    for attachment in message.attachments:
        if attachment.type == MessagesMessageAttachmentType.PHOTO:
            string_at += await re_upload_photo(attachment.photo, 'photo.jpg')
            string_at += "\n"
    await m.reply(string_at)


@bot.on.private_message(AdminPanelCommand("рп"))
async def update_rp_commands(m: Message):
    command = m.text.lower()[3:]
    strings = []
    message = await m.get_full_message()
    for i, attachment in enumerate(message.attachments):
        if attachment.type == attachment.type.PHOTO:
            await download_photo(attachment.photo, f"{i}{command}.jpg")
            string = await bot_photo_message_upl.upload(f"{i}{command}.jpg")
            strings.append(string)
            os.remove(f"{i}{command}.jpg")
    array = await db.select([db.RPCommand.photos]).where(db.RPCommand.command == command).gino.scalar()
    if array is None:
        array = []
    array += strings
    await db.RPCommand.update.values(photos=array).where(db.RPCommand.command == command).gino.status()
    await m.reply("Добавил")


@bot.on.private_message(AdminPanelCommand('апи '))
async def api_request(m: Message):
    text = m.text[4:]
    method, *params = text.split(maxsplit=1)
    if params:
        params = json.loads(params[0])
    else:
        params = {}
    response = await bot.api.request(method, params)
    await m.reply(response)
