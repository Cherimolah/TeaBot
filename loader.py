from vkbottle import Bot
from config import BOT_TOKEN
import sys
import loguru
from middlewares.registration import RegistrationMiddleware
from blueprints.blueprint import bp
import handlers

bot = Bot(BOT_TOKEN)
bp.load(bot)

bot.labeler.message_view.register_middleware(RegistrationMiddleware)

loguru.logger.remove()
loguru.logger.add(sys.stdout, level="INFO")
