import asyncio
import os
from loader import bot
from vkbottle.bot import Message, MessageEvent
from vkbottle.dispatch.rules.base import AttachmentTypeRule, PayloadMapRule
from keyboards.private import formats, boards
from vkbottle import GroupEventType
from glue.glue_photos import glue
from config import GROUP_ID, BOT_TOKEN
from vkbottle import PhotoMessageUploader
from vkbottle.bot import Bot
from vkbottle import VKAPIError
from PIL import Image, ImageDraw, ImageFont
from utils.photos import get_max_photo


glue_users = {}
photo_uploader = PhotoMessageUploader(Bot(BOT_TOKEN).api)


@bot.on.private_message(AttachmentTypeRule("photo"))
async def glue_photos(m: Message):
    message = (await bot.api.messages.get_by_id(m.id)).items[0]
    for att in message.attachments:
        if att.type != att.type.PHOTO:
            await bot.reply_msg(m, "Для склейки убери всё лишнее и оставь только фото")
            break
    if len(message.attachments) == 1:
        await bot.reply_msg(m, "Для склейки надо больше 1 фотки")
        return
    glue_users[m.from_id] = {"photos": [get_max_photo(x.photo) for x in message.attachments],
                             "format": None, "boards": None}
    await bot.reply_msg(m, "Выбери формат склейки:", keyboard=formats[len(message.attachments)-2])


@bot.on.private_message(PayloadMapRule({"columns": int, "upper": int, "lower": int}))
@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, PayloadMapRule({"columns": int, "upper": int, "lower": int}))
async def set_format(event: MessageEvent):
    glue_users[event.object.user_id]['columns'] = event.payload['columns']
    glue_users[event.object.user_id]['upper'] = bool(event.payload['upper'])
    glue_users[event.object.user_id]['lower'] = bool(event.payload['lower'])
    await bot.change_msg(event, "Выбери рамки", keyboard=boards)


@bot.on.private_message(PayloadMapRule({"boards": bool, "color": str}))
@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, PayloadMapRule({"boards": bool, "color": str}))
async def set_boards(event: MessageEvent):
    glue_users[event.object.user_id]['boards'] = event.payload['boards']
    glue_users[event.object.user_id]['color'] = event.payload['color']
    await bot.change_msg(event, "🫖 Чайник достаёт свой волшебный клей")
    params = glue_users[event.object.user_id]
    await glue(params['photos'], params['columns'], params['upper'], params['lower'], params['boards'],
               params['color'], event.user_id)
    reply = "⛄ Держи склееные фотографии"

    if not await bot.api.groups.is_member(GROUP_ID, event.object.user_id):
        reply += ". Чтобы отключить водяной знак подпишись на сообщество 🌠"
        font = ImageFont.truetype("data/ua-BRAND-regular.otf", size=40)
        img = Image.open(f"{event.user_id}.jpg")
        img_draw = ImageDraw.Draw(img)
        img_draw.text((0, 0), "Склеено чайным ботом", font=font)
        img.save(f"{event.user_id}.jpg")

    devided = False
    while True:
        try:
            photo = await photo_uploader.upload(f"{event.user_id}.jpg")
            break
        except VKAPIError[100]:
            devided = True
            img = Image.open(f"{event.user_id}.jpg")
            img = img.resize((int(img.size[0]*0.9), int(img.size[1]*0.9)))
            img.save(f"{event.user_id}.jpg")
            await asyncio.sleep(0.2)
    if devided:
        reply += ". Фото пришлось немного сжать, потому что вк не принимал такие большие размеры"
    os.remove(f"{event.user_id}.jpg")
    del glue_users[event.user_id]
    await bot.write_msg(event.user_id, reply, attachment=photo)
