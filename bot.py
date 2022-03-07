from loader import bot
import traceback
import time
from datetime import datetime, timedelta
from ongoing.chat_updater import update_chats
from ongoing.schedule import stats_notification


@bot.error_handler.register_error_handler(Exception)
async def exception(e: Exception):
    print((datetime.utcfromtimestamp(time.time())+timedelta(hours=5)).strftime("%d.%m.%Y %H:%M:%S"))
    print(e)
    print(traceback.format_exc())

if __name__ == '__main__':
    bot.loop_wrapper.add_task(update_chats())
    bot.loop_wrapper.add_task(stats_notification())
    bot.run_forever()
