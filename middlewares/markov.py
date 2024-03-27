import re
from abc import ABC
from random import randint

from vkbottle.dispatch.middlewares import BaseMiddleware
from vkbottle.bot import Message

from db_api.db_engine import db
from utils.parsing_users import mention_regex
from utils.views import generate_text
from loader import bot


link_regex = re.compile("(https:\/\/www\.|http:\/\/www\.|https:\/\/|http:\/\/)?[a-zA-Z]{2,}(\.[a-zA-Z]{2,})(\.[a-zA-Z]{2,})?\/[a-zA-Z0-9]{2,}|((https:\/\/www\.|http:\/\/www\.|https:\/\/|http:\/\/)?[a-zA-Z]{2,}(\.[a-zA-Z]{2,})(\.[a-zA-Z]{2,})?)|(https:\/\/www\.|http:\/\/www\.|https:\/\/|http:\/\/)?[a-zA-Z0-9]{2,}\.[a-zA-Z0-9]{2,}\.[a-zA-Z0-9]{2,}(\.[a-zA-Z0-9]{2,})?")


class MarkovMiddleware(BaseMiddleware[Message], ABC):

    async def post(self):
        if self.event.peer_id > 2_000_000_000 and not self.handlers and self.event.from_id > 0:
            text = mention_regex.sub("", self.event.text)
            text = link_regex.sub("", text)
            if text:
                await db.Message.create(text=text)

            if randint(1, 20) == 7:  # 1/20 chance
                await bot.api.messages.send(peer_id=self.event.peer_id,
                                            message=await generate_text(),
                                            random_id=0)


bot.labeler.message_view.register_middleware(MarkovMiddleware)
