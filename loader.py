import sys
import loguru
from typing import Dict

from vkbottle.user import User
from vkbottle.bot import Bot
from vkbottle.framework.labeler.bot import BotLabeler
from pyqiwip2p import AioQiwiP2P

from bots.bot_extended import APIExtended, RawBotEventViewExtended, BotMessageViewExtended, AioHTTPClientExtended, \
    BotPollingExtended
from config import BOT_TOKEN, USER_TOKEN, QIWI_TOKEN, confirmation_code, secret_key, GROUP_ID

client = AioHTTPClientExtended()

bot = Bot(api=APIExtended(BOT_TOKEN, http_client=client),
          labeler=BotLabeler(raw_event_view=RawBotEventViewExtended(),
                             message_view=BotMessageViewExtended()),
          polling=BotPollingExtended())
evg = User(api=APIExtended(USER_TOKEN, http_client=client))
evg.api.API_VERSION = '5.134'

qiwi = AioQiwiP2P(QIWI_TOKEN)

loguru.logger.remove()
loguru.logger.add(sys.stdout, level="INFO")

captcha_users: Dict[int, int] = {}
