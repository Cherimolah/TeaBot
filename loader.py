import sys
import loguru

from vkbottle.user import User
from vkbottle.bot import Bot
from vkbottle.framework.labeler.bot import BotLabeler
from pyqiwip2p import AioQiwiP2P
from db_api.db_engine import db
from fastapi import FastAPI, BackgroundTasks, Request, Response

from bots.bot_extended import APIExtended, RawBotEventViewExtended, BotMessageViewExtended, AioHTTPClientExtended
from config import BOT_TOKEN, USER_TOKEN, QIWI_TOKEN, confirmation_code, secret_key, GROUP_ID

client = AioHTTPClientExtended()

bot = Bot(api=APIExtended(BOT_TOKEN, http_client=client),
          labeler=BotLabeler(raw_event_view=RawBotEventViewExtended(),
                             message_view=BotMessageViewExtended()))
evg = User(api=APIExtended(USER_TOKEN, http_client=AioHTTPClientExtended()))

qiwi = AioQiwiP2P(QIWI_TOKEN)

loguru.logger.remove()
loguru.logger.add(sys.stdout, level="INFO")

app = FastAPI()


@app.post('/tea_bot')
async def handle_callback(request: Request, background_task: BackgroundTasks):
    try:
        data = await request.json()
    except:
        return Response("not today", status_code=403)

    event = await db.select([db.Event.event_id]).where(db.Event.event_id == data['event_id']).gino.scalar()
    if event:  # Event is stored
        return Response('ok')

    if data["type"] == "confirmation" and abs(data['group_id']) == abs(GROUP_ID):
        return Response(confirmation_code)

    if data["secret"] == secret_key:
        background_task.add_task(bot.process_event, data)
        await db.Event.create(event_id=data['event_id'])
    return Response("ok")
