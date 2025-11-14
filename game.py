from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core.game_logic import FoolGame
from keyboards.builders import MenuKeyboards

game_router = Router()
keyboards = MenuKeyboards()

class GameStates(StatesGroup):
    in_game = State()

active_games = {}

@game_router.callback_query(F.data.startswith("diff_"))
async def start_bot_game(callback: CallbackQuery, state: FSMContext):
    """Начало игры с ботом"""
    difficulty = callback.data.replace("diff_", "")
    
    # Создаем новую игру
    game = FoolGame(difficulty)
    game.deal_cards()
    active_games[callback.from_user.id] = game
    
    await state.set_state(GameStates.in_game)
    
    await callback.message.edit_text(
        f"🎮 Игра с ботом началась! ({difficulty} уровень)\n\n"
        f"{game.get_game_state()}",
        reply_markup=keyboards.get_game_keyboard(game)
    )

@game_router.callback_query(F.data.startswith("play_"))
async def play_card(callback: CallbackQuery, state: FSMContext):
    """Игрок ходит картой"""
    user_id = callback.from_user.id
    if user_id not in active_games:
        await callback.answer("Игра не найдена. Начни новую!")
        return
    
    game = active_games[user_id]
    card_index = int(callback.data.replace("play_", ""))
    
    # Определяем тип хода
    if game.current_action == "attack" or game.current_action == "add":
        result = game.player_attack(card_index)
    elif game.current_action == "defend":
        result = game.player_defend(card_index)
    else:
        result = "Неизвестное действие"
    
    await process_game_turn(callback, game, user_id, state, result)

@game_router.callback_query(F.data == "take_cards")
async def take_cards(callback: CallbackQuery, state: FSMContext):
    """Игрок забирает карты"""
    user_id = callback.from_user.id
    if user_id not in active_games:
        await callback.answer("Игра не найдена")
        return
    
    game = active_games[user_id]
    result = game.player_take_cards()
    
    await process_game_turn(callback, game, user_id, state, result)

@game_router.callback_query(F.data == "pass_turn")
async def pass_turn(callback: CallbackQuery, state: FSMContext):
    """Игрок пасует"""
    user_id = callback.from_user.id
    if user_id not in active_games:
        await callback.answer("Игра не найдена")
        return
    
    game = active_games[user_id]
    result = game.player_pass()
    
    await process_game_turn(callback, game, user_id, state, result)

async def process_game_turn(callback, game, user_id, state, player_result):
    """Обработка хода игры"""
    # Проверяем конец игры
    game.check_game_over()
    
    if game.game_over:
        await handle_game_over(callback, game, user_id, state)
        return
    
    # Ход бота (если не конец раунда)
    if not game.round_over:
        bot_move = game.bot_make_move()
        game.check_game_over()
    else:
        bot_move = "🎯 Раунд окончен"
        game.round_over = False
    
    # Снова проверяем конец игры после хода бота
    if game.game_over:
        await handle_game_over(callback, game, user_id, state)
        return
    
    # Обновляем сообщение
    response_text = f"🎮 {player_result}\n\n"
    if bot_move:
        response_text += f"🤖 {bot_move}\n\n"
    response_text += game.get_game_state()
    
    await callback.message.edit_text(
        response_text,
        reply_markup=keyboards.get_game_keyboard(game)
    )

async def handle_game_over(callback, game, user_id, state):
    """Обработка конца игры"""
    if game.winner == "player":
        text = "🎉 Ты победил! Бот остался в дураках!"
    elif game.winner == "bot":
        text = "😞 Бот победил! Попробуй еще раз!"
    else:
        text = "🤝 Ничья!"
    
    await callback.message.edit_text(
        f"{text}\n\n{game.get_game_state()}",
        reply_markup=keyboards.back_to_menu()
    )
    
    # Обновляем статистику
    from database import db
    db.update_user_stats(user_id, won=(game.winner == "player"))
    
    # Удаляем игру
    if user_id in active_games:
        del active_games[user_id]
    await state.clear()

@game_router.callback_query(F.data == "surrender")
async def surrender(callback: CallbackQuery, state: FSMContext):
    """Игрок сдается"""
    user_id = callback.from_user.id
    
    await callback.message.edit_text(
        "🏳️ Ты сдался! Бот победил!",
        reply_markup=keyboards.back_to_menu()
    )
    
    if user_id in active_games:
        del active_games[user_id]
    await state.clear()