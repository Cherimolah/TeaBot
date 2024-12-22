import traceback
from datetime import datetime, timedelta, timezone
import asyncio
from contextlib import asynccontextmanager
from typing import Annotated

import uvicorn
from fastapi import FastAPI, Response, Request, BackgroundTasks, Form, HTTPException
from ayoomoney.types import NotificationBase

from config import ADMIN_ID, DEBUG, YOOMONEY_TOKEN
from loader import bot
from ongoing.schedule import scheduler
from ongoing.database_updater import update_users, update_users_in_chats, load_punisments
from db_api.db_engine import db
from utils.views import refill_balance

import handlers
import middlewares
from handlers.rp_commands import add_rp_commands
from config import secret_key, confirmation_code, GROUP_ID


def number_error():
    i = 1
    while True:
        yield i
        i += 1


err_num = number_error()


@bot.error_handler.register_error_handler(Exception)
async def exception(e: Exception):
    print((datetime.now(timezone(timedelta(hours=5)))).strftime("%d.%m.%Y %H:%M:%S"))
    num = next(err_num)
    print(f"[ERROR] №{num}: {e}")
    print(traceback.format_exc(), "\n")
    await bot.api.messages.send(peer_id=ADMIN_ID, message=f"⚠ [Ошибка] №{num}:"
                                                          f"\n{traceback.format_exc()}", random_id=0)


async def load_tasks():
    await db.connect()
    await add_rp_commands()
    scheduler.start()
    asyncio.create_task(update_users())
    asyncio.create_task(update_users_in_chats())
    asyncio.create_task(load_punisments())


@asynccontextmanager
async def lifespan(app: FastAPI):
    await load_tasks()
    yield


app = FastAPI(lifespan=lifespan)


@app.post('/event')
async def handle_callback(request: Request, background_task: BackgroundTasks):
    try:
        data = await request.json()
    except:
        return Response("not today", status_code=403)

    if data["type"] == "confirmation" and abs(data['group_id']) == abs(GROUP_ID):
        return Response(confirmation_code)

    event = await db.select([db.Event.event_id]).where(db.Event.event_id == data['event_id']).gino.scalar()
    if event:  # Event is stored
        return Response('ok')

    if data["secret"] == secret_key:
        background_task.add_task(bot.process_event, data)
        await db.Event.create(event_id=data['event_id'])
    return Response("ok")


@app.post('/notification')
async def new_order(data: Annotated[NotificationBase, Form()], background_task: BackgroundTasks):
    is_valid_hash = data.check_sha1_hash(YOOMONEY_TOKEN)
    if is_valid_hash is False:
        return Response(status_code=403, content="i'm busy")
    reciever = int(data.label.split('|')[0])
    amount = int(data.withdraw_amount)
    background_task.add_task(refill_balance, reciever, amount)
    return Response(status_code=200, content="ok")

if __name__ == '__main__':
    if DEBUG:
        bot.loop_wrapper.on_startup.append(load_tasks())
        bot.run_forever()
    else:
        uvicorn.run(app, log_level='error', port=8001)
