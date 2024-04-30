import asyncio
import random
import datetime

from typing import Tuple
from vkbottle.bot import Message, MessageEvent
from vkbottle.dispatch.rules.base import PayloadRule, PayloadMapRule
from vkbottle import Keyboard, Callback, KeyboardButtonColor, GroupEventType
from sqlalchemy import func

from loader import bot
from db_api.db_engine import db
import keyboards
from utils.custom_rules import GameExists


async def send_roulette_info(user_id: int):
    data = (await db.select([db.User.dollars, db.User.win_dollars, db.User.wins])
            .where(db.User.user_id == user_id).gino.first())
    top_list = [x[0] for x in await db.select([db.User.user_id])
    .order_by(db.User.win_dollars.desc())
    .order_by(db.User.dollars.desc()).order_by(db.User.wins.desc()).order_by(db.User.user_id.asc()).gino.all()]
    position = top_list.index(user_id)
    await bot.api.messages.send(message="🔫 Здесь ты можешь сыграть в чайную рулетку с ботом "
                                        "(скоро появится рулетка с другими игроками)\n\n"
                   f"💸 Баланс: {data.dollars}\n"
                   f"🍵💸 Выиграно: {data.win_dollars}\n"
                   f"🍵 Побед: {data.wins}\n"
                   f"🏆 Место в топе: {position + 1}",
                   keyboard=keyboards.private.roulette, peer_id=user_id)


async def check_end_game(game_id) -> bool:
    game = await db.RouletteGame.get(game_id)
    if game.lives1 <= 0 or game.lives2 <= 0:
        if game.lives1 <= 0:
            await bot.api.messages.send(
                message=f"К сожалению вы проиграли в этой схватке.\nИтого: -{game.bet}💸\n", peer_id=game.player1, keyboard=Keyboard())
            if game.player2:
                await db.User.update.values(dollars=db.User.dollars + int(game.bet) * 0.94,
                                            win_dollars=db.User.win_dollars + int(game.bet) * 0.94,
                                            wins=db.User.wins + 1).where(
                    db.User.user_id == game.player2).gino.status()
                await bot.api.messages.send(peer_id=game.player2,
                                            message=f"Поздравляем вы выиграли в этой схватке!\n\nИтого: +{int(game.bet) * 0.94}💸", keyboard=Keyboard())
        else:  # lives2 = 0
            await db.User.update.values(dollars=db.User.dollars + int(game.bet) * 0.94,
                                        win_dollars=db.User.win_dollars + int(game.bet) * 0.94,
                                        wins=db.User.wins + 1).where(
                db.User.user_id == game.player1).gino.status()
            await bot.api.messages.send(
                message=f"Поздравляем! Вы победили в этой схваткe!\nИтого: +{int(game.bet) * 0.94}💸", peer_id=game.player1, keyboard=Keyboard())
            if game.player2:
                await bot.api.messages.send(message=f"К сожалению в проиграли в этой схватке.\nИтого: -{game.bet}💸\n", peer_id=game.player2, keyboard=Keyboard())
        await db.RouletteGame.delete.where(db.RouletteGame.id == game_id).gino.status()
        await send_roulette_info(game.player1)
        if game.player2:
            await send_roulette_info(game.player2)
        await db.RouletteGame.delete.where(db.RouletteGame.id == game_id).gino.status()
        return True
    return False


async def fill_cups(game_id):
    game = await db.RouletteGame.get(game_id)
    if game.tea == 0 and game.coffee == 0:
        coffee = random.randint(3, 7)
        tea = 8 - coffee
        await db.RouletteGame.update.values(coffee=coffee, tea=tea).where(db.RouletteGame.id == game_id).gino.status()
        await bot.api.messages.send(message="Похоже у нас закончились чашки!\nЗагружаем новые", peer_id=game.player1)
        if game.player2:
            await bot.api.messages.send(message="Похоже у нас закончились чашки!\nЗагружаем новые", peer_id=game.player2)
        await asyncio.sleep(2)


async def step_bot(game_id: int):
    game = await db.RouletteGame.get(game_id)
    self_drink = False
    if game.tea > game.coffee:
        self_drink = True
    elif game.tea == game.coffee:
        self_drink = bool(random.randint(0, 1))
    if self_drink:
        await bot.api.messages.send(message="Бот решает выпить чашку сам", peer_id=game.player1)
    else:
        await bot.api.messages.send(message="Бот решает напоить тебя! Что же там окажется....", peer_id=game.player1)
    await asyncio.sleep(2)
    step = random.randint(1, game.tea + game.coffee)
    if self_drink:
        if step <= game.tea:
            await db.RouletteGame.update.values(tea=db.RouletteGame.tea - 1).where(db.RouletteGame.id == game_id).gino.status()
            await bot.api.messages.send(message="Бот выпивает чашку и это оказывается чай. Он не получает урон", peer_id=game.player1)
            await bot.api.messages.send("Следующим ходит бот")
            await asyncio.sleep(2)
        else:
            await db.RouletteGame.update.values(coffee=db.RouletteGame.coffee - 1).where(db.RouletteGame.id == game_id).gino.status()
            await db.RouletteGame.update.values(lives2=db.RouletteGame.lives2 - 1).where(db.RouletteGame.id == game_id).gino.status()
            await bot.api.messages.send(message="Бот выпивает чашку и это оказывается кофе! Бот получил урон", peer_id=game.player1)
            if await check_end_game(game_id):
                return
    else:
        await db.RouletteGame.update.values(step=1).where(db.RouletteGame.id == game_id).gino.status()
        if step <= game.tea:
            await db.RouletteGame.update.values(tea=db.RouletteGame.tea - 1).where(db.RouletteGame.id == game_id).gino.status()
            await bot.api.messages.send(message="Бот напоил тебя чашкой чая! Ты не получаешь урон", peer_id=game.player1)
        else:
            await db.RouletteGame.update.values(coffee=db.RouletteGame.coffee - 1).where(db.RouletteGame.id == game_id).gino.status()
            await db.RouletteGame.update.values(lives1=db.RouletteGame.lives1 - 1).where(db.RouletteGame.id == game_id).gino.status()
            await bot.api.messages.send(message="Бот напоил тебя чашкой кофе! Ты получил урон", peer_id=game.player1)
            if await check_end_game(game_id):
                return
    await bot.api.messages.send(message="Слеующий ход твой", peer_id=game.player1)
    await fill_cups(game_id)
    game = await db.RouletteGame.get(game_id)
    await bot.api.messages.send(message=f"Жизни: Вы {'❤️' * game.lives1}/{'❤️' * game.lives2} Бот\n"
                       f"Чашки: {game.coffee}☕/{game.tea}🍵\n\n", keyboard=keyboards.generators.roulette_game(game_id),
                                peer_id=game.player1)


@bot.on.private_message(PayloadRule({"main_menu": "roulette"}))
async def roulette_info(m: Message):
    await send_roulette_info(m.from_id)


@bot.on.private_message(PayloadRule({"roulette": "bot"}))
async def roulette_bot(m: Message):
    await m.answer("Выбери ставку на которой будешь играть", keyboard=keyboards.generators.get_bets(False))


@bot.on.private_message(PayloadMapRule({"roulette_bet": int, "player": bool}))
async def create_game(m: Message):
    bet = m.payload['roulette_bet']
    balance = await db.select([db.User.dollars]).where(db.User.user_id == m.from_id).gino.scalar()
    if bet > balance:
        return "Недостаточно средств на балансе!"
    await db.User.update.values(dollars=db.User.dollars - bet).where(
        db.User.user_id == m.from_id).gino.status()
    if not m.payload['player']:
        coffee = random.randint(3, 7)
        tea = 8 - coffee
        game = await db.RouletteGame.create(player1=m.from_id, lives1=3, lives2=3, round_number=1, step=1,
                                            coffee=coffee, tea=tea, bet=bet)
        await m.answer("Игра началась!\n\n"
                       "Жизни: Ты ❤️❤️❤️/❤️❤️❤️ Бот\n"
                       f"Чашки: {coffee}☕/{tea}🍵\n\n"
                       f"Ход ваш!", keyboard=keyboards.generators.roulette_game(game.id))


@bot.on.private_message(PayloadMapRule({"game_id": int, "drink": int}), GameExists())
async def drink(m: Message, game: db.RouletteGame):
    game_id = m.payload['game_id']
    player_drink = m.payload['drink']
    cups = ['t'] * game.tea + ['c'] * game.coffee
    cup = random.choice(cups)
    if cup == 'c':  # Coffee do damage
        await db.RouletteGame.update.values(coffee=db.RouletteGame.coffee - 1).where(
            db.RouletteGame.id == game_id).gino.status()
        if player_drink == 1:
            await db.RouletteGame.update.values(lives1=db.RouletteGame.lives1 - 1).where(
                db.RouletteGame.id == game_id).gino.status()
            await m.answer("Ты выпиваешь чашку и она оказалась с кофе. -1 сердечко ((", keyboard=Keyboard())
        elif player_drink == 2:
            await db.RouletteGame.update.values(lives2=db.RouletteGame.lives2 - 1).where(
                db.RouletteGame.id == game_id).gino.status()
            await m.answer("Ты напоил соперника чашкой кофе! Он получил урон", keyboard=Keyboard())
        else:
            return "Давай не ломай бота! Вас там двое в игре куда ещё"
    else:
        await db.RouletteGame.update.values(tea=db.RouletteGame.tea - 1).where(db.RouletteGame.id == game_id).gino.status()
        if player_drink == 1:
            await m.answer("Ты выпил чашку и она оказалась с чаем! Жизнь спасена", keyboard=Keyboard())
        elif player_drink == 2:
            await m.answer("Ты напоили соперника чашкой чая. Возможно, он поблагодарствует тебе", keyboard=Keyboard())
        else:
            return "Давай не ломай бота! Вас там двое в игре куда ещё"

    if await check_end_game(game_id):
        return

    await fill_cups(game_id)

    await asyncio.sleep(2)
    if not game.player2:
        if player_drink == 1 and cup == 't':
            await m.answer("Следующий ход твой")
            game = await db.RouletteGame.get(game_id)
            await bot.api.messages.send(message=f"Жизни: Вы {'❤️' * game.lives1}/{'❤️' * game.lives2} Бот\n"
                                                f"Чашки: {game.coffee}☕/{game.tea}🍵\n\n",
                                        keyboard=keyboards.generators.roulette_game(game_id),
                                        peer_id=game.player1)
            return
        await db.RouletteGame.update.values(step=2).where(db.RouletteGame.id == game_id).gino.status()
        await m.answer("Следующим ходит бот", keyboard=Keyboard())
        await asyncio.sleep(2)
        await step_bot(game_id)

    # TODO


async def page_top_roulette(page: int) -> Tuple[str, Keyboard]:
    data = (await db.select([db.User.user_id, db.User.win_dollars]).order_by(db.User.win_dollars.desc())
            .order_by(db.User.dollars.desc()).order_by(db.User.wins.desc()).order_by(db.User.user_id.asc())
            .offset((page - 1) * 15).limit(15).gino.all())
    count = await db.select([func.count(db.User.user_id)]).gino.scalar()
    if count % 15 == 0:
        pages = int(count // 15)
    else:
        pages = int(count // 15) + 1
    reply = f"Топ игроков рулетки по выигранным 💸:\n\nСтраница {page}/{pages}\n\n"
    for i, tup in enumerate(data):
        user_id, win_dollars = tup
        reply += f"{i + 1}. {await db.get_mention_user(user_id, 0)} {win_dollars} 💸\n"
    keyboard = None
    if pages > 1:
        keyboard = Keyboard(inline=True)
    if page > 1:
        keyboard.add(
            Callback("<-", {"roulette_top_page": page - 1}), KeyboardButtonColor.SECONDARY
        )
    if page < pages:
        keyboard.add(
            Callback("->", {"roulette_top_page": page + 1}), KeyboardButtonColor.SECONDARY
        )
    return reply, keyboard


@bot.on.private_message(PayloadRule({"roulette": "top"}))
async def top_roulette(m: Message):
    reply, keyboard = await page_top_roulette(1)
    await m.answer(reply, keyboard=keyboard)


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent, PayloadMapRule({"roulette_top_page": int}))
async def pagination_top_roulette(m: MessageEvent):
    reply, keyboard = await page_top_roulette(m.payload['roulette_top_page'])
    await m.edit_message(reply, keyboard=keyboard.get_json())


@bot.on.private_message(PayloadRule({"roulette": "free"}))
async def free_roulette(m: Message):
    dollars, last_bonus = await db.select([db.User.dollars, db.User.last_bonus]).where(db.User.user_id == m.from_id).gino.first()
    if dollars >= 1450:
        return "Бонус доступен, если у вас меньше 1450 💸"
    if last_bonus and last_bonus > (datetime.datetime.now() - datetime.timedelta(hours=4)):
        return "Бонус доступен только раз в 4 часа!"
    await db.User.update.values(dollars=db.User.dollars + 1450, last_bonus=datetime.datetime.now()).where(db.User.user_id == m.from_id).gino.status()
    balance = await db.select([db.User.dollars]).where(db.User.user_id == m.from_id).gino.scalar()
    return f"✅ Вы получили 1450 💸\nБаланс: {balance} 💸"
