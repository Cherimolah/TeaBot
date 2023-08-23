from datetime import datetime, timedelta
from loader import bot, evg
from db_api.db_engine import db
from config import ADMIN_ID, GROUP_ID
from aiohttp import ClientSession
import json
from bs4 import BeautifulSoup
from utils.scheduler import AsyncIOScheduler, Interval, Cron

scheduler = AsyncIOScheduler()


@scheduler.add_task(Cron(hour=12, minute=38, second=59))
async def stats_notification():
    day = datetime.now().date()
    stats = await db.select([*db.StatsTotal]).where(db.StatsTotal.date == day).gino.first()
    if not stats:
        await bot.write_msg(ADMIN_ID, f"За {day.strftime('%d.%m.%Y')} статистики нет")
    else:
        await bot.write_msg(ADMIN_ID, f"Статистика за {day.strftime('%d.%m.%Y')}:\n\n"
                                     f"Принято сообщений: {stats[1]}\n"
                                     f"Отправлено сообщений: {stats[2]}\n"
                                     f"Отредактировано сообщений: {stats[3]}\n"
                                     f"Отправлено ответов: {stats[4]}\n\n"
                                     f"Общая активность: {stats[1] + stats[2] + stats[3] + stats[4]}")


@scheduler.add_task(Interval(hours=1))
async def kombucha_reduce():
    await db.User.update.values(kombucha=db.User.kombucha - 0.05).where(db.User.kombucha > 100).gino.status()


@scheduler.add_task(Interval(minutes=10))
async def set_online():
    try:
        await bot.api.groups.enable_online(GROUP_ID)
    except:
        pass

today = datetime.now()
next_minute = datetime(today.year, today.month, today.day, today.hour, 0, 0) + timedelta(minutes=1)


@scheduler.add_task(Interval(hours=12), next_run_time=next_minute)
async def update_stickers():
    last_id = await db.select([db.Sticker.id]).order_by(db.Sticker.id.desc()).limit(1).gino.scalar()
    if not last_id:
        last_id = 0
    st_info = await evg.api.request("store.getStockItems", {"type": "stickers",
                                                               "product_ids": list(range(last_id+1, last_id+150))})
    packs = st_info['response']['items']
    for pack in packs:
        if not pack:
            continue
        await db.Sticker.create(id=pack['product']['id'], name=pack['product']['title'], price=pack.get("price") or 0)


