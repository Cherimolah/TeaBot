from vkbottle import Bot
from config import BOT_TOKEN
import sys
import loguru
from middlewares.registration import RegistrationMiddleware
from middlewares.stats import StatsMessagesMiddleware
from middlewares.muted_user import MutedUserMiddleware
from blueprints.blueprint import bp
import handlers

bot = Bot(BOT_TOKEN)
bp.load(bot)

bot.labeler.message_view.register_middleware(RegistrationMiddleware)
bot.labeler.message_view.register_middleware(StatsMessagesMiddleware)
bot.labeler.message_view.register_middleware(MutedUserMiddleware)

loguru.logger.remove()
loguru.logger.add(sys.stdout, level="SUCCESS")
