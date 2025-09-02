import sys
import loguru
from typing import Dict, List

from vkbottle.user import User
from vkbottle.bot import Bot
from vkbottle.framework.labeler.bot import BotLabeler
from ayoomoney.wallet import YooMoneyWalletAsync
from openai import AsyncOpenAI
from aiogram import Bot as TGBot
from aiogram.client.telegram import TelegramAPIServer
from aiogram.client.bot import AiohttpSession

from bots.bot_extended import APIExtended, RawBotEventViewExtended, BotMessageViewExtended, AioHTTPClientExtended, RouterExtended, ErrorHandlerExtended
from config import BOT_TOKEN, USER_TOKEN, YOOMONEY_TOKEN, AI_API_KEYS, ILYA_TOKEN, TG_TOKEN

client = AioHTTPClientExtended()

bot = Bot(api=APIExtended(BOT_TOKEN, http_client=client),
          labeler=BotLabeler(raw_event_view=RawBotEventViewExtended(),
                             message_view=BotMessageViewExtended()),
          router=RouterExtended(), error_handler=ErrorHandlerExtended())

bot.labeler.vbml_ignore_case = True
bot.api.API_URL = 'https://api.vk.ru/method/'
evg = User(api=APIExtended(USER_TOKEN, http_client=client))
evg.api.API_VERSION = '5.134'
ilya = User(api=APIExtended(ILYA_TOKEN, http_client=client))

session = AiohttpSession(api=TelegramAPIServer.from_base('http://localhost:8081'))
tg_bot = TGBot(token=TG_TOKEN, session=session)

yoomoney = YooMoneyWalletAsync(YOOMONEY_TOKEN)

loguru.logger.remove()
loguru.logger.add(sys.stdout, level="INFO")

captcha_users: Dict[int, int] = {}

ai_clients: List[AsyncOpenAI] = [AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key) for api_key in AI_API_KEYS]
