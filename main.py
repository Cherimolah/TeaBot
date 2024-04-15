import traceback
from datetime import datetime, timedelta, timezone
import asyncio

import uvicorn

from config import ADMIN_ID, DEBUG
from loader import bot, app
from ongoing.schedule import scheduler
from ongoing.database_updater import update_users, update_users_in_chats, load_punisments
from db_api.db_engine import db

import handlers
import middlewares
from handlers.rp_commands import add_rp_commands


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


@app.on_event("startup")
async def load_tasks():
    await db.connect()
    await add_rp_commands()
    scheduler.start()
    asyncio.create_task(update_users())
    asyncio.create_task(update_users_in_chats())
    asyncio.create_task(load_punisments())


if __name__ == '__main__':
    if DEBUG:
        bot.loop_wrapper.on_startup.append(load_tasks())
        bot.run_forever()
    else:
        uvicorn.run(app, log_level='error')
