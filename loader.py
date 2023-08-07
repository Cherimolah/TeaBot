from config import BOT_TOKEN, USER_TOKEN, QIWI_TOKEN, confirmation_code, secret_key, GROUP_ID, webdriver_path
import sys
import loguru
from bots.bot_extended import MyBot
from vkbottle.user import User
from pyqiwip2p import AioQiwiP2P
from db_api.db_engine import db
from pyppeteer import launch
from fastapi import FastAPI, BackgroundTasks, Request, Response

bot = MyBot(BOT_TOKEN)
evg = User(USER_TOKEN)

qiwi = AioQiwiP2P(QIWI_TOKEN)

loguru.logger.remove()
loguru.logger.add(sys.stdout, level="INFO")

app = FastAPI()
browser = None


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


@app.on_event("startup")
async def on_startup():
    await db.connect()
    global browser
    browser = await launch(
        headless=True,
        executablePath=webdriver_path,
        args=[
            '--no-sandbox',
            '--single-process',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--no-zygote'
        ])
