from vkbottle.bot import Message
from vkbottle.dispatch.rules.base import PayloadRule, PayloadMapRule

from loader import bot
from db_api.db_engine import db
import keyboards


@bot.on.private_message(PayloadRule({"main_menu": "roulette"}))
async def roulette_info(m: Message):
    data = (await db.select([db.User.dollars, db.User.win_dollars, db.User.wins])
            .where(db.User.user_id == m.from_id).gino.first())
    top_list = [x[0] for x in await db.select([db.User.user_id])
    .order_by(db.User.win_dollars.desc())
    .order_by(db.User.dollars.desc()).order_by(db.User.user_id.asc()).gino.all()]
    position = top_list.index(m.from_id)
    await m.answer("🔫 Здесь ты можешь сыграть в русскую рулетку с другим человеком или с ботом\n\n"
                   f"💸 Баланс: {data.dollars}\n"
                   f"🍵💸 Выиграно: {data.win_dollars}\n"
                   f"🍵 Побед: {data.wins}\n"
                   f"🏆 Место в топе: {position + 1}",
                   keyboard=keyboards.private.roulette)


@bot.on.private_message(PayloadRule({"roulette": "bot"}))
async def roulette_bot(m: Message):
    await m.answer("Выбери ставку на которой будешь играть", keyboard=keyboards.private.get_bets(False))


@bot.on.private_message(PayloadMapRule({"roulette_bet": int, "player": bool}))
async def create_game(m: Message):
    bet = m.payload['roulette_bet']
    balance = await db.select([db.User.dollars]).where(db.User.user_id == m.from_id).gino.scalar()
    if bet > balance:
        return "Недостаточно средств на балансе!"
    if not m.payload['player']:
        game = await db.RouletteGame.create(player1=m.from_id, lives_1=3, lives_2=3, round_number=1)

