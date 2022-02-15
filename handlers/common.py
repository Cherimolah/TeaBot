from blueprints.blueprint import bp
from vkbottle.bot import Message
from db.main_database import main_db


@bp.on.message(text="бот")
async def echo(m: Message):
    await m.reply("На месте")
