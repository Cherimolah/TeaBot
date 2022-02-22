from blueprints.blueprint import bp
from vkbottle.bot import Message


@bp.on.message(text="бот")
async def echo(m: Message):
    await m.reply("На месте")
