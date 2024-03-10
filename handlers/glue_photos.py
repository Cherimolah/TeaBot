import asyncio
import os
from typing import Union

from loader import bot
from vkbottle.bot import Message, MessageEvent
from vkbottle.dispatch.rules.base import AttachmentTypeRule, PayloadMapRule
from keyboards.private import formats, boards
from vkbottle import GroupEventType
from glue.glue_photos import glue
from config import GROUP_ID, FONT_PATH
from bots.uploaders import bot_photo_message_upl
from vkbottle import VKAPIError
from PIL import Image, ImageDraw, ImageFont
from utils.photos import get_max_photo
from vkbottle_types.responses.messages import MessagesSendUserIdsResponseItem


glue_users = {}


@bot.on.private_message(PayloadMapRule({"a": int}))
async def g(m: Message):
    return "nnn"


@bot.on.private_message(AttachmentTypeRule("photo"))
async def glue_photos(m: Message):
    message = (await bot.api.messages.get_by_id(m.id)).items[0]
    for att in message.attachments:
        if att.type != att.type.PHOTO:
            await m.reply("Для склейки убери всё лишнее и оставь только фото")
            break
    if len(message.attachments) == 1:
        await m.reply("Для склейки надо больше 1 фотки")
        return
    glue_users[m.from_id] = {"photos": [get_max_photo(x.photo) for x in message.attachments],
                             "format": None, "boards": None}
    message = await m.reply("Выбери формат склейки:", keyboard=formats[len(message.attachments)-2])
    glue_users[m.from_id]['message'] = message


@bot.on.private_message(PayloadMapRule({"columns": int, "upper": int, "lower": int}))
@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, PayloadMapRule({"columns": int, "upper": int, "lower": int}))
async def set_format(event: Union[MessageEvent, Message]):
    glue_users[event.peer_id]['columns'] = event.payload['columns']
    glue_users[event.peer_id]['upper'] = bool(event.payload['upper'])
    glue_users[event.peer_id]['lower'] = bool(event.payload['lower'])
    if isinstance(event, MessageEvent):
        await event.edit_message("Выбери рамки", keyboard=boards)
    else:
        message: MessagesSendUserIdsResponseItem = glue_users[event.peer_id]['message']
        await bot.api.messages.delete([message.message_id], delete_for_all=True)
        message = await event.answer("Выбери рамки", keyboard=boards)
        glue_users[event.peer_id]['message'] = message


@bot.on.private_message(PayloadMapRule({"boards": bool, "color": str}))
@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, PayloadMapRule({"boards": bool, "color": str}))
async def set_boards(event: Union[Message, MessageEvent]):
    glue_users[event.peer_id]['boards'] = event.payload['boards']
    glue_users[event.peer_id]['color'] = event.payload['color']
    if isinstance(event, MessageEvent):
        await event.edit_message("🫖 Чайник достаёт свой волшебный клей")
    else:
        message: MessagesSendUserIdsResponseItem = glue_users[event.peer_id]['message']
        await bot.api.messages.delete([message.message_id], delete_for_all=True)
        message = await event.answer("🫖 Чайник достаёт свой волшебный клей")
        glue_users[event.peer_id]['message'] = message
    params = glue_users[event.peer_id]
    await glue(params['photos'], params['columns'], params['upper'], params['lower'], params['boards'],
               params['color'], event.peer_id)
    reply = "⛄ Держи склееные фотографии"

    if not await bot.api.groups.is_member(GROUP_ID, event.peer_id):
        reply += ". Чтобы отключить водяной знак подпишись на сообщество 🌠"
        font = ImageFont.truetype(FONT_PATH, size=40)
        img = Image.open(f"{event.peer_id}.jpg")
        img_draw = ImageDraw.Draw(img)
        img_draw.text((0, 0), "Склеено чайным ботом", font=font, fill=(255, 0, 0))
        img.save(f"{event.peer_id}.jpg")

    devided = False
    while True:
        try:
            photo = await bot_photo_message_upl.upload(f"{event.peer_id}.jpg")
            break
        except VKAPIError[100]:
            devided = True
            img = Image.open(f"{event.peer_id}.jpg")
            img = img.resize((int(img.size[0]*0.9), int(img.size[1]*0.9)))
            img.save(f"{event.peer_id}.jpg")
            await asyncio.sleep(0.2)
    if devided:
        reply += ". Фото пришлось немного сжать, потому что вк не принимал такие большие размеры"
    os.remove(f"{event.peer_id}.jpg")
    del glue_users[event.peer_id]
    await bot.api.messages.send(event.peer_id, reply, attachment=photo)
