from datetime import datetime
from blueprints.blueprint import bp
import time
import asyncio
from db.main_database import MainDB
from config import ADMIN_ID


async def stats_notification():
    main_db = await MainDB().connection()
    while True:
        day = datetime.now().date()
        to_time = time.mktime(datetime(day.year, day.month, day.day, hour=23, minute=59, second=59).timetuple())
        await asyncio.sleep(to_time-time.time())
        await main_db.sql.execute("SELECT * FROM stats WHERE date = ?", (day,))
        stats = await main_db.sql.fetchone()
        if stats is None:
            await bp.write_msg(ADMIN_ID, f"За {day.strftime('%d.%m.%Y')} статистики нет")
        else:
            await bp.write_msg(ADMIN_ID, f"Статистика за {day.strftime('%d.%m.%Y')}:\n\n"
                                         f"Принято сообщений: {stats[1]}\n"
                                         f"Отправлено сообщений: {stats[2]}\n"
                                         f"Отредактировано сообщений: {stats[3]}\n"
                                         f"Отправлено ответов: {stats[4]}\n\n"
                                         f"Общая активность: {stats[1]+stats[2]+stats[3]+stats[4]}")
        await asyncio.sleep(20)
