from vkbottle import Bot
from config import BOT_TOKEN
import sys
import loguru
from blueprints.blueprint import bp
import handlers

bot = Bot(BOT_TOKEN)
bp.load(bot)

loguru.logger.remove()
loguru.logger.add(sys.stdout, level="INFO")
