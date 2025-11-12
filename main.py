import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

import config
from database import SessionLocal, Player, ActiveGame, Tournament, create_tables
from game_logic import GameEngine, Card
from keyboards import *
from states import GameStates, MultiplayerStates
from payment import process_stars_payment

# Реплики Дастина
DASTIN_QUOTES = {
    "win": [
        "🎉 ТЫ ВЫИГРАЛ! Держи шоколад! 🍫",
        "⚡ МОЩНО! Ты реально прокачался!",
        "👑 КОРОЛЬ ДУРАКА! Забирай звёзды!",
    ],
    "lose": [
        "😞 Проиграл? Не беда! Шоколад исправит! 🍫",
        "💀 Жестко... Но мы ещё отыграемся!",
        "🤖 Бот тебя сделал... В следующий раз будет иначе!"
    ],
    "daily": [
        "🎁 ДЕРЖИ ПОДАРОК! Шоколад уже в пути! 🍫",
        "💫 ЗВЁЗДОПАД! Лови награду!",
        "🍀 УДАЧА НА ТВОЕЙ СТОРОНЕ! Забирай звёзды!"
    ]
}

async def send_dastin_sticker(chat_id: int, sticker_type: str):
    """Отправка стикеров Дастина"""
    stickers = {
        "win": "CAACAgIAAxkBAAEL...",  # Замени на реальные ID стикеров
        "lose": "CAACAgIAAxkBAAEL...", 
        "celebration": "CAACAgIAAxkBAAEL..."
    }
    if sticker_type in stickers:
        await bot.send_sticker(chat_id, stickers[sticker_type])

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token="8525915886:AAEMqKR9PVNWbRm9jqOhuLGDyBWrHqwXtfQ")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

game_engine = GameEngine()
# Глобальная переменная для лобби
waiting_players = {}

@router.callback_query(F.data.startswith("mp_"))
async def create_multiplayer(callback: CallbackQuery):
    user_id = callback.from_user.id
    players_count = int(callback.data.replace("mp_", ""))
    
    # Создаем лобби
    lobby_id = f"lobby_{user_id}_{int(datetime.now().timestamp())}"
    waiting_players[lobby_id] = {
        "creator": user_id,
        "players": [user_id],
        "max_players": players_count,
        "created_at": datetime.now()
    }
    
    await callback.message.edit_text(
        f"👥 Лобби создано! Ожидаем игроков...\n"
        f"✅ Вы (1/{players_count})\n\n"
        f"Пригласительная ссылка:\n"
        f"https://t.me/{(await bot.get_me()).username}?start={lobby_id}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔁 Обновить", callback_data=f"refresh_{lobby_id}")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="play_menu")]
        ])
    )
# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def get_card_from_string(card_str: str) -> Card:
    """Преобразование строки в карту"""
    suit = card_str[-1]  # Последний символ - масть
    rank = card_str[:-1]  # Все кроме последнего - достоинство
    return Card(suit, rank)

async def send_game_state(game: ActiveGame, message: Message = None, callback: CallbackQuery = None):
    """Отправка текущего состояния игры"""
    players_data = game.players
    current_player = game.current_player
    
    text = f"🎮 Игра в Дурака\nКозырь: {game.trump}\n\n"
    
    for user_id, player_data in players_data.items():
        username = player_data["username"]
        cards_count = len(player_data["cards"])
        turn_indicator = "🎯" if user_id == current_player else "  "
        
        if player_data.get("is_ai", False):
            text += f"{turn_indicator} {username} (Бот) - {cards_count} карт\n"
        else:
            text += f"{turn_indicator} {username} - {cards_count} карт\n"
    
    text += f"\nСтол: {', '.join(game.table['attacks']) if game.table['attacks'] else 'Пусто'}"
    
    if message:
        await message.answer(text)
    elif callback:
        await callback.message.answer(text)

# ==================== ОСНОВНЫЕ КОМАНДЫ ====================

@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    with SessionLocal() as session:
        player = session.get(Player, user_id)
        if not player:
            player = Player(user_id=user_id, username=username)
            session.add(player)
            session.commit()
            welcome = "🎉 Добро пожаловать в Дурака Онлайн!"
        else:
            welcome = "С возвращением в Дурака Онлайн!"
    
    await message.answer(
        f"{welcome}\nВыберите действие:",
        reply_markup=main_menu()
    )

# ==================== ГЛАВНОЕ МЕНЮ ====================

@router.callback_query(F.data == "main_menu")
async def main_menu_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=main_menu()
    )

@router.callback_query(F.data == "play_menu")
async def play_menu_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎮 Выберите режим игры:",
        reply_markup=play_menu()
    )

@router.callback_query(F.data == "profile")
async def profile_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    with SessionLocal() as session:
        player = session.get(Player, user_id)
        
        skin_name = config.SKINS.get(player.selected_skin, {}).get("name", "Стандартный")
        
        await callback.message.edit_text(
            f"👤 Профиль игрока:\n"
            f"📛 Имя: {player.username}\n"
            f"⭐ Звёзды: {player.stars}\n"
            f"🎮 Сыграно игр: {player.games_played}\n"
            f"🏆 Побед: {player.games_won}\n"
            f"💎 Выиграно турниров: {player.tournaments_won}\n"
            f"🎨 Текущий скин: {skin_name}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎨 Магазин скинов", callback_data="skins_shop")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
            ])
        )

# ==================== ИГРА С БОТОМ ====================

@router.callback_query(F.data == "bot_game")
async def bot_game_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "🤖 Выберите сложность бота:",
        reply_markup=bot_difficulty()
    )

@router.callback_query(F.data.in_(["bot_easy", "bot_medium", "bot_hard"]))
async def start_bot_game(callback: CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.username or callback.from_user.first_name
    difficulty = callback.data
    
    difficulty_names = {
        "bot_easy": "😊 Легкий",
        "bot_medium": "😐 Средний", 
        "bot_hard": "😈 Сложный"
    }
    
    with SessionLocal() as session:
        # Создаем настоящую игру
        game_id = f"bot_{user_id}_{int(datetime.now().timestamp())}"
        
        # Создаем колоду и раздаем карты
        deck = game_engine.create_deck()
        game_engine.shuffle_deck(deck)
        trump = deck[0].suit if deck else random.choice(game_engine.SUITS)
        hands = game_engine.deal_cards(deck, 2)
        
        game = ActiveGame(
            game_id=game_id,
            players={
                str(user_id): {
                    "username": username, 
                    "cards": [str(card) for card in hands[0]], 
                    "is_ai": False
                },
                "0": {
                    "username": f"Бот ({difficulty_names[difficulty]})", 
                    "cards": [str(card) for card in hands[1]], 
                    "is_ai": True
                }
            },
            player_order=[user_id, 0],
            current_player=user_id,
            deck=[str(card) for card in deck],
            table={"attacks": [], "defends": []},
            trump=trump,
            game_type=difficulty
        )
        session.add(game)
        session.commit()
        
        # Обновляем статистику
        player = session.get(Player, user_id)
        player.games_played += 1
        session.commit()
    
    await callback.message.edit_text(
        f"🎮 Игра с ботом началась!\n"
        f"🃏 Козырь: {trump}\n"
        f"💪 Сложность: {difficulty_names[difficulty]}\n\n"
        f"📋 Ваши карты:\n{', '.join([str(card) for card in hands[0]])}\n\n"
        f"🎯 Ваш ход! Выберите карту для атаки:",
        reply_markup=cards_keyboard([str(card) for card in hands[0]], "attack")
    )

@router.callback_query(F.data.startswith("attack_"))
async def process_attack(callback: CallbackQuery):
    user_id = callback.from_user.id
    card_str = callback.data.replace("attack_", "")
    
    with SessionLocal() as session:
        game = session.query(ActiveGame).filter(
            ActiveGame.current_player == user_id,
            ActiveGame.status == "active"
        ).first()
        
        if not game:
            await callback.answer("Игра не найдена!", show_alert=True)
            return
        
        # Проверяем можно ли атаковать
        card = get_card_from_string(card_str)
        if not game_engine.can_attack(card, game.table):
            await callback.answer("Нельзя атаковать этой картой!", show_alert=True)
            return
        
        # Атакуем
        game.table["attacks"].append(card_str)
        game.players[str(user_id)]["cards"].remove(card_str)
        
        # Ход бота
        bot_cards = [get_card_from_string(c) for c in game.players["0"]["cards"]]
        defend_card = None
        
        if game.game_type == "bot_easy":
            defend_card = game_engine.bot_move_easy(bot_cards, game.table, game.trump)
        elif game.game_type == "bot_medium":
            defend_card = game_engine.bot_move_medium(bot_cards, game.table, game.trump)
        else:
            defend_card = game_engine.bot_move_hard(bot_cards, game.table, game.trump)
        
        if defend_card:
            # Бот отбился
            game.table["defends"].append(str(defend_card))
            game.players["0"]["cards"].remove(str(defend_card))
            await callback.message.answer("🤖 Бот успешно отбился!")
        else:
            # Бот взял карты
            for card in game.table["attacks"]:
                game.players["0"]["cards"].append(card)
            game.table = {"attacks": [], "defends": []}
            await callback.message.answer("🤖 Бот не смог отбиться и взял карты!")
        
        # Проверяем победу
        if not game.players[str(user_id)]["cards"]:
            await callback.message.answer("🎉 ТЫ ВЫИГРАЛ! +50 звёзд!")
            player = session.get(Player, user_id)
            player.games_won += 1
            player.stars += 50
        elif not game.players["0"]["cards"]:
            await callback.message.answer("😞 Бот выиграл...")
            player = session.get(Player, user_id)
            player.games_played += 1
        
        session.commit()
    
    await callback.message.edit_text(
        "Игра продолжается!",
        reply_markup=main_menu()
    )
    
    with SessionLocal() as session:
        # Создаем настоящую игру
        game_id = f"bot_{user_id}_{int(datetime.now().timestamp())}"
        
        # Создаем колоду и раздаем карты
        deck = game_engine.create_deck()
        game_engine.shuffle_deck(deck)
        trump = deck[0].suit if deck else random.choice(game_engine.SUITS)
        hands = game_engine.deal_cards(deck, 2)
        
        game = ActiveGame(
            game_id=game_id,
            players={
                str(user_id): {
                    "username": username, 
                    "cards": [str(card) for card in hands[0]], 
                    "is_ai": False
                },
                "0": {
                    "username": f"Бот ({difficulty_names[difficulty]})", 
                    "cards": [str(card) for card in hands[1]], 
                    "is_ai": True
                }
            },
            player_order=[user_id, 0],
            current_player=user_id,
            deck=[str(card) for card in deck],
            table={"attacks": [], "defends": []},
            trump=trump,
            game_type=difficulty
        )
        session.add(game)
        session.commit()
        
        # Обновляем статистику
        player = session.get(Player, user_id)
        player.games_played += 1
        session.commit()
    
    await callback.message.edit_text(
        f"🎮 Игра с ботом началась!\n"
        f"🃏 Козырь: {trump}\n"
        f"💪 Сложность: {difficulty_names[difficulty]}\n\n"
        f"📋 Ваши карты:\n{', '.join([str(card) for card in hands[0]])}\n\n"
        f"🎯 Ваш ход! Выберите карту для атаки:",
        reply_markup=cards_keyboard([str(card) for card in hands[0]], "attack")
    )

# ==================== МУЛЬТИПЛЕЕР (ЗАГЛУШКА) ====================

@router.callback_query(F.data == "multiplayer")
async def multiplayer_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "👥 Мультиплеер режим:\n\n"
        "Выберите количество игроков:",
        reply_markup=multiplayer_menu()
    )

# ==================== ТУРНИРЫ (ЗАГЛУШКА) ====================

@router.callback_query(F.data == "tournaments")
async def tournaments_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏆 Турнирная система:\n\n"
        "🎯 Создай турнир и пригласи друзей!\n"
        "💰 Призовой фонд: 500+ звёзд",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎯 Создать турнир", callback_data="create_tournament")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
        ])
    )

@router.callback_query(F.data == "create_tournament")
async def create_tournament(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    with SessionLocal() as session:
        tournament = Tournament(
            tournament_id=f"tournament_{user_id}_{int(datetime.now().timestamp())}",
            name="Ежедневный турнир",
            players=[user_id],
            prize_pool=500,
            entry_fee=50
        )
        session.add(tournament)
        session.commit()
    
    await callback.message.edit_text(
        "🏆 Турнир создан!\n"
        "💰 Призовой фонд: 500 звёзд\n"
        "🎫 Взнос: 50 звёзд\n\n"
        "Ожидаем игроков...",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Присоединиться", callback_data="join_tournament")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="tournaments")]
        ])
    )



# ==================== МАГАЗИН СКИНОВ ====================

@router.callback_query(F.data == "skins_shop")
async def skins_shop_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    with SessionLocal() as session:
        player = session.get(Player, user_id)
        
        skins_text = "🛍️ Магазин скинов:\n\n"
        keyboard = []
        
        for skin_id, skin_data in config.SKINS.items():
            emoji = "✅" if skin_id in player.skins else "⭐"
            status = "Куплено" if skin_id in player.skins else f"{skin_data['price']} звёзд"
            
            skins_text += f"{emoji} {skin_data['name']} - {status}\n"
            
            if skin_id not in player.skins:
                keyboard.append([InlineKeyboardButton(
                    text=f"🛒 Купить {skin_data['name']} - {skin_data['price']}⭐",
                    callback_data=f"buy_skin_{skin_id}"
                )])
            elif skin_id != player.selected_skin:
                keyboard.append([InlineKeyboardButton(
                    text=f"🎯 Выбрать {skin_data['name']}",
                    callback_data=f"select_skin_{skin_id}"
                )])
        
        keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="profile")])
        
        await callback.message.edit_text(
            skins_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )

@router.callback_query(F.data.startswith("buy_skin_"))
async def buy_skin_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    skin_id = callback.data.replace("buy_skin_", "")
    
    with SessionLocal() as session:
        player = session.get(Player, user_id)
        skin_data = config.SKINS.get(skin_id)
        
        if not skin_data:
            await callback.answer("Ошибка: скин не найден!", show_alert=True)
            return
            
        if skin_id in player.skins:
            await callback.answer("У вас уже есть этот скин!", show_alert=True)
            return
            
        if player.stars < skin_data['price']:
            await callback.answer("Недостаточно звёзд!", show_alert=True)
            return
            
        # Покупка скина
        player.stars -= skin_data['price']
        player.skins.append(skin_id)
        player.selected_skin = skin_id
        session.commit()
        
        await callback.answer(f"Скин {skin_data['name']} куплен!", show_alert=True)
        await skins_shop_handler(callback)

# ==================== ПОКУПКА ЗВЁЗД ====================

@router.callback_query(F.data == "buy_stars")
async def buy_stars_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "💫 Покупка звёзд:\n"
        "Звёзды можно использовать для:\n"
        "• Покупки крутых скинов 🎨\n"
        "• Участия в платных турнирах 🏆\n"
        "• Особых возможностей в игре\n\n"
        "Выберите пакет:",
        reply_markup=stars_keyboard()
    )

@router.callback_query(F.data.startswith("buy_"))
async def process_stars_purchase(callback: CallbackQuery):
    package = callback.data.replace("buy_", "")
    amount = config.STAR_PACKAGES.get(package, 0)
    
    if amount == 0:
        await callback.answer("Ошибка выбора пакета!", show_alert=True)
        return
    
    # РАБОЧАЯ ЗАГЛУШКА (пока не подключена ЮKassa)
    success = await process_stars_payment(callback.from_user.id, amount)
    if success:
        await callback.answer(f"Получено {amount} звёзд! 💫", show_alert=True)
        await main_menu_handler(callback)
    
    # ЗАГЛУШКА - убираем автоматическое начисление
    # success = await process_stars_payment(callback.from_user.id, amount)
    # if success:
    #     await callback.answer(f"Получено {amount} звёзд! 💫", show_alert=True)

# ==================== ЕЖЕДНЕВНАЯ НАГРАДА ====================

@router.callback_query(F.data == "daily_reward")
async def daily_reward_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    now = datetime.now()
    
    with SessionLocal() as session:
        player = session.get(Player, user_id)
        
        if player.daily_reward:
            # Проверяем, прошло ли больше 24 часов
            time_diff = now - player.daily_reward
            if time_diff.total_seconds() < 24 * 3600:  # 24 часа
                hours_left = 24 - int(time_diff.total_seconds() / 3600)
                await callback.answer(
                    f"⏳ Следующая награда через {hours_left} часов!",
                    show_alert=True
                )
                return
        
        reward = random.randint(50, 150)
        player.stars += reward
        player.daily_reward = now
        session.commit()
        
        await callback.answer(f"🎉 Вы получили {reward} звёзд!", show_alert=True)
        await callback.message.edit_text(
            f"🎁 Ежедневная награда!\n"
            f"💫 Получено: {reward} звёзд\n"
            f"💰 Теперь у вас: {player.stars} звёзд",
            reply_markup=main_menu()
        )

# ==================== СТАТИСТИКА И ЛИДЕРБОРД ====================

@router.callback_query(F.data == "stats")
async def stats_handler(callback: CallbackQuery):
    with SessionLocal() as session:
        # Топ-10 игроков по победам
        top_players = session.query(Player).order_by(Player.games_won.desc()).limit(10).all()
        
        leaderboard = "🏆 Топ игроков:\n\n"
        for i, player in enumerate(top_players, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            leaderboard += f"{medal} {player.username} - {player.games_won} побед\n"
        
        # Статистика текущего игрока
        current_player = session.get(Player, callback.from_user.id)
        if current_player:
            win_rate = (current_player.games_won / current_player.games_played * 100) if current_player.games_played > 0 else 0
            leaderboard += f"\n📊 Ваша статистика:\n"
            leaderboard += f"Победы: {current_player.games_won}/{current_player.games_played}\n"
            leaderboard += f"Винрейт: {win_rate:.1f}%\n"
            leaderboard += f"Турниры: {current_player.tournaments_won}"
    
    await callback.message.edit_text(
        leaderboard,
        reply_markup=main_menu()
    )

# ==================== ПРАВИЛА ИГРЫ ====================

@router.callback_query(F.data == "rules")
async def rules_handler(callback: CallbackQuery):
    rules_text = (
        "📚 Правила игры в Дурака:\n\n"
        "🎯 Цель игры: избавиться от всех карт первым\n\n"
        "🃏 Ход игры:\n"
        "• Игроки по очереди атакуют и защищаются\n"
        "• Атаковать можно картой того же достоинства, что уже лежит на столе\n"
        "• Защищаться нужно картой старше той же масти или козырем\n"
        "• Если не можешь защититься - забираешь все карты со стола\n"
        "• Можно подкидывать карты того же достоинства, что уже на столе\n\n"
        "⚡ Особенности:\n"
        "• Козырь бьёт любую карту другой масти\n"
        "• Можно атаковать сразу несколькими картами\n"
        "• Игрок, который отбился, становится следующим атакующим\n\n"
        "🎮 В нашем боте:\n"
        "• ⏰ На ход даётся 2 минуты\n"
        "• ⭐ Звёзды - валюта для скинов и турниров\n"
        "• 🏆 Турниры - соревнования с призовым фондом\n"
        "• 🎨 Скины - визуальное оформление карт"
    )
    
    await callback.message.edit_text(
        rules_text,
        reply_markup=main_menu()
    )

# ==================== ЗАПУСК БОТА ====================

async def main():
    logger.info("Создание таблиц...")
    create_tables()
    
    logger.info("Запуск бота Дурак Онлайн...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())