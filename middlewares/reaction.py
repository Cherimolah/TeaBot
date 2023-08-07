from vkbottle.dispatch.middlewares import BaseMiddleware
from vkbottle.bot import Message

from loader import bot
from db_api.db_engine import db


class ReactionMiddleware(BaseMiddleware[Message]):

    async def post(self) -> None:
        reaction = await db.select([db.User.reaction]).where(db.User.user_id == self.event.from_id).gino.scalar()
        if reaction:
            await bot.api.request("messages.sendReaction", {"peer_id": self.event.peer_id,
                                                            "cmid": self.event.conversation_message_id,
                                                            "reaction_id": reaction})


bot.labeler.message_view.register_middleware(ReactionMiddleware)
