import sys
import loguru
from typing import Dict

from vkbottle.user import User
from vkbottle.bot import Bot
from vkbottle.framework.labeler.bot import BotLabeler
from ayoomoney.wallet import YooMoneyWalletAsync

from bots.bot_extended import APIExtended, RawBotEventViewExtended, BotMessageViewExtended, AioHTTPClientExtended, RouterExtended, ErrorHandlerExtended
from config import BOT_TOKEN, USER_TOKEN, YOOMONEY_TOKEN

client = AioHTTPClientExtended()

bot = Bot(api=APIExtended(BOT_TOKEN, http_client=client),
          labeler=BotLabeler(raw_event_view=RawBotEventViewExtended(),
                             message_view=BotMessageViewExtended()),
          router=RouterExtended(), error_handler=ErrorHandlerExtended())

bot.labeler.vbml_ignore_case = True
evg = User(api=APIExtended(USER_TOKEN, http_client=client))
evg.api.API_VERSION = '5.134'

yoomoney = YooMoneyWalletAsync(YOOMONEY_TOKEN)

loguru.logger.remove()
loguru.logger.add(sys.stdout, level="INFO")

captcha_users: Dict[int, int] = {}
