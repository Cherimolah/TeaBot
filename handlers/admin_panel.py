import os

import aiohttp

from loader import bot
from vkbottle.bot import Message, Bot
from config import ADMIN_ID, BOT_TOKEN
from db_api.db_engine import db
from vkbottle_types.objects import MessagesMessageAttachmentType, PhotosPhoto
from vkbottle import PhotoMessageUploader

from utils.photos import download_photo
from bots.uploaders import bot_photo_message_upl
from utils.custom_rules import AdminPanelCommand


photo_m = PhotoMessageUploader(Bot(BOT_TOKEN).api)


def get_link_max_photo(photo: PhotosPhoto):
    square = 0
    max_index = 0
    for index, size in enumerate(photo.sizes):
        if size.height * size.width >= square:
            square = size.height * size.width
            max_index = index
    return photo.sizes[max_index].url


@bot.on.private_message(AdminPanelCommand("скл "))
async def sql_injection(m: Message):
    sql_script = m.text[4:]
    result = await db.all(sql_script)
    await bot.api.messages.send(ADMIN_ID, message=f"Результат выполнения скрипта:", random_id=0)
    for i in range(0, len(str(result)), 4096):
        await bot.api.messages.send(ADMIN_ID, message=str(result)[i:i+4096], random_id=0)


@bot.on.private_message(AdminPanelCommand("аттач бот"))
async def get_attachment_string(m: Message):
    message = (await bot.api.messages.get_by_id(m.id)).items[0]
    string_at = ""
    for attachment in message.attachments:
        if attachment.type == MessagesMessageAttachmentType.PHOTO:
            link_photo = get_link_max_photo(attachment.photo)
            async with aiohttp.ClientSession() as session:
                response = await session.get(link_photo)
                photo = await response.read()
            string_at += await photo_m.upload(photo)
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

