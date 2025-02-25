from datetime import datetime, timedelta, date, timezone
from loader import bot, evg
from db_api.db_engine import db
from config import ADMIN_ID, GROUP_ID
import asyncio
from utils.scheduler import AsyncIOScheduler, Interval, Cron
from sqlalchemy import and_, or_

scheduler = AsyncIOScheduler()
today = datetime.now()
next_minute = datetime(today.year, today.month, today.day, today.hour, today.minute, 0, tzinfo=timezone(timedelta(hours=3))) + timedelta(minutes=1)
next_hour = datetime(today.year, today.month, today.day, today.hour, 0, 0, tzinfo=timezone(timedelta(hours=3))) + timedelta(hours=1)


@scheduler.add_task(Cron(hour=23, minute=59, second=59))
async def stats_notification():
    day = datetime.now().date()
    stats = await db.select([*db.StatsTotal]).where(db.StatsTotal.date == day).gino.first()
    if not stats:
        await bot.api.messages.send(ADMIN_ID, f"За {day.strftime('%d.%m.%Y')} статистики нет")
    else:
        await bot.api.messages.send(ADMIN_ID, f"Статистика за {day.strftime('%d.%m.%Y')}:\n\n"
                                              f"Принято сообщений: {stats[1]}\n"
                                              f"Отправлено сообщений: {stats[2]}\n"
                                              f"Отредактировано сообщений: {stats[3]}\n"
                                              f"Отправлено ответов: {stats[4]}\n\n"
                                              f"Общая активность: {stats[1] + stats[2] + stats[3] + stats[4]}")


@scheduler.add_task(Interval(hours=1), next_run_time=next_hour)
async def kombucha_reduce():
    await db.User.update.values(kombucha=db.User.kombucha - 0.05).where(
        and_(db.User.kombucha >= 100, db.User.kombucha < 500)).gino.status()
    await db.User.update.values(kombucha=db.User.kombucha * 0.99).where(db.User.kombucha >= 500).gino.status()


@scheduler.add_task(Interval(minutes=10))
async def set_online():
    try:
        await bot.api.groups.enable_online(GROUP_ID)
    except:
        pass


@scheduler.add_task(Interval(hours=1), next_run_time=next_minute)
async def update_stickers():
    last_id = await db.select([db.Sticker.id]).order_by(db.Sticker.id.desc()).limit(1).gino.scalar()
    if not last_id:
        last_id = 0
    st_info = await evg.api.request('store.getStockItems',
                                    {'type': 'stickers', 'product_ids': ','.join(map(str, list(range(last_id + 1, last_id + 150))))})
    packs = st_info['response']['items']
    for pack in packs:
        if not pack:
            continue
        await db.Sticker.create(id=pack['product']['id'], name=pack['product']['title'], price=pack.get("price") or 0)


@scheduler.add_task(Cron(hour=0, minute=0, second=2))
async def congratulation_birthday():
    user_ids = await db.select([db.User.user_id, db.User.birthday]).where(db.User.birthday.isnot(None)).gino.all()
    now = date.today()
    for user_id, birthday in user_ids:
        if birthday.month == now.month and birthday.day == now.day:
            chat_ids = [x[0] for x in
                        await db.select([db.UserToChat.chat_id]).where(
                            and_(db.UserToChat.user_id == user_id, db.UserToChat.in_chat.is_(True))).gino.all()]
            reply = f"🎉🎊 Поздравляем {await db.get_mention_user(user_id, 3)} с Днём Рождения!!\n"
            if birthday.year != 1800:
                reply += f"Сегодня тебе исполняется {now.year - birthday.year} лет! "
            else:
                reply += "Сегодня тебе исполняется... Та хер его знает сколько тебе исполняется. Поскрывают года " \
                         "в своих профилях, а я потом гадать должен! Но, наверное, ты уже "
                if await db.is_woman_user(user_id):
                    reply += "взрослая крутая асинхронная тян! "
                else:
                    reply += "взрослый крутой асинхронный кун! "
            reply += "Желаю тебе счастья, здоровья, успехов и всего самого наилучшего! Пей побольше чая и поменьше кофе"
            for chat_id in chat_ids:
                await bot.api.messages.send(chat_id + 2000000000, reply,
                                            attachment="photo-201071106_457240771_7de9eaa806e40d06be",
                                            disable_mentions=False)
                await asyncio.sleep(0.2)
            if not chat_ids:
                await bot.api.messages.send(user_id, reply, attachment="photo-201071106_457240771_7de9eaa806e40d06be",
                                            disable_mentions=False)


@scheduler.add_task(Interval(hours=1))
async def clear_old_events():
    yesterday = datetime.now() - timedelta(days=1)
    await db.Event.delete.where(or_(db.Event.created_at < yesterday, db.Event.created_at.is_(None))).gino.status()
