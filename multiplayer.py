from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import json

from database import db
from keyboards.builders import MenuKeyboards

multiplayer_router = Router()
keyboards = MenuKeyboards()

class MultiplayerStates(StatesGroup):
    joining_lobby = State()
    in_multiplayer_game = State()

@multiplayer_router.message(F.text == "👥 Мультиплеер")
async def multiplayer_main(message: Message):
    """Главное меню мультиплеера"""
    user_id = message.from_user.id
    
    # Принудительно очищаем пользователя из всех лобби при входе в меню
    db.delete_user_from_all_lobbies(user_id)
    
    await message.answer(
        "👥 Мультиплеер - РАБОТАЕТ! 🎮\n\n"
        "Создай лобби и пригласи друзей!\n\n"
        "Выбери действие:",
        reply_markup=keyboards.multiplayer_main()
    )

async def show_lobby_info(message, lobby_id: int, players: list):
    """Показать информацию о лобби"""
    players_count = len(players)
    creator_id = players[0]
    
    text = f"🎪 Лобби #{lobby_id} - АКТИВНО\n\n"
    text += f"👥 Игроков: {players_count}/5\n"
    text += f"🆔 ID для друзей: {lobby_id}\n\n"
    text += "📋 Игроки в лобби:\n"
    
    for i, player_id in enumerate(players, 1):
        text += f"{i}. Игрок {player_id}\n"
    
    is_creator = message.from_user.id == creator_id
    
    if is_creator and players_count >= 2:
        text += "\n✅ МОЖНО НАЧИНАТЬ ИГРУ!"
    elif players_count < 2:
        text += "\n⏳ Ждем еще игроков..."
    else:
        text += "\n⏳ Ожидаем начала игры..."
    
    if isinstance(message, CallbackQuery):
        await message.message.edit_text(
            text,
            reply_markup=keyboards.lobby_management(lobby_id, is_creator)
        )
    else:
        await message.answer(
            text,
            reply_markup=keyboards.lobby_management(lobby_id, is_creator)
        )

@multiplayer_router.callback_query(F.data == "force_leave_lobby")
async def force_leave_lobby(callback: CallbackQuery):
    """Принудительный выход из всех лобби"""
    user_id = callback.from_user.id
    
    # Удаляем пользователя из всех лобби
    db.delete_user_from_all_lobbies(user_id)
    
    await callback.message.edit_text(
        "✅ Ты вышел из всех лобби!\n\n"
        "Теперь можешь создать новое или присоединиться к существующему.",
        reply_markup=keyboards.multiplayer_main()
    )

@multiplayer_router.callback_query(F.data.startswith("delete_lobby_"))
async def delete_lobby(callback: CallbackQuery):
    """Удалить лобби (только для создателя)"""
    lobby_id = int(callback.data.replace("delete_lobby_", ""))
    user_id = callback.from_user.id
    
    lobby = db.get_lobby(lobby_id)
    if not lobby:
        await callback.answer("Лобби не найдено!", show_alert=True)
        return
    
    players = json.loads(lobby[2])
    
    # Проверяем что пользователь - создатель
    if players[0] != user_id:
        await callback.answer("Только создатель может удалить лобби!", show_alert=True)
        return
    
    # Удаляем лобби
    db.delete_lobby(lobby_id)
    
    await callback.message.edit_text(
        "🗑️ Лобби удалено!\n\n"
        "Все игроки были выгнаны.",
        reply_markup=keyboards.multiplayer_main()
    )

@multiplayer_router.callback_query(F.data.startswith("start_real_game_"))
async def start_real_multiplayer_game(callback: CallbackQuery, state: FSMContext):
    """Начать настоящую мультиплеерную игру"""
    lobby_id = int(callback.data.replace("start_real_game_", ""))
    user_id = callback.from_user.id
    
    lobby = db.get_lobby(lobby_id)
    if not lobby:
        await callback.answer("Лобби не найдено!", show_alert=True)
        return
    
    players = json.loads(lobby[2])
    
    if players[0] != user_id:
        await callback.answer("Только создатель лобби может начать игру!", show_alert=True)
        return
    
    if len(players) < 2:
        awaitcallback.answer("Нужно минимум 2 игрока для начала игры!", show_alert=True)
        return
    
    # Помечаем лобби как играющее
    db.start_lobby_game(lobby_id)
    
    await callback.message.edit_text(
        f"🎮 МУЛЬТИПЛЕЕРНАЯ ИГРА НАЧАЛАСЬ! 🎉\n\n"
        f"Лобби #{lobby_id}\n"
        f"👥 Игроков: {len(players)}\n"
        f"🎯 Первый ход: Игрок {players[0]}\n\n"
        f"Игра началась! Делайте ходы по очереди!\n\n"
        f"⚡ Режим мультиплеера активирован!",
        reply_markup=keyboards.multiplayer_game_interface(lobby_id)
    )

@multiplayer_router.callback_query(F.data.startswith("mp_play_"))
async def multiplayer_play_card(callback: CallbackQuery, state: FSMContext):
    """Ход в мультиплеерной игре"""
    lobby_id = int(callback.data.replace("mp_play_", ""))
    user_id = callback.from_user.id
    
    lobby = db.get_lobby(lobby_id)
    if not lobby:
        await callback.answer("Игра не найдена!", show_alert=True)
        return
    
    players = json.loads(lobby[2])
    
    # Простая логика хода
    current_player_index = players.index(user_id)
    next_player_index = (current_player_index + 1) % len(players)
    next_player = players[next_player_index]
    
    await callback.message.edit_text(
        f"🎮 Мультиплеер - Ход завершен!\n\n"
        f"✅ Игрок {user_id} сделал ход\n"
        f"🎯 Следующий ход: Игрок {next_player}\n\n"
        f"Продолжаем игру!",
        reply_markup=keyboards.multiplayer_game_interface(lobby_id)
    )

@multiplayer_router.callback_query(F.data.startswith("mp_surrender_"))
async def multiplayer_surrender(callback: CallbackQuery, state: FSMContext):
    """Сдача в мультиплеерной игре"""
    lobby_id = int(callback.data.replace("mp_surrender_", ""))
    user_id = callback.from_user.id
    
    # Удаляем лобби
    db.delete_lobby(lobby_id)
    
    await callback.message.edit_text(
        f"🏳️ Игрок {user_id} сдался!\n\n"
        f"Мультиплеерная игра завершена.",
        reply_markup=keyboards.multiplayer_main()
    )
    await state.clear()

@multiplayer_router.callback_query(F.data.startswith("mp_status_"))
async def multiplayer_status(callback: CallbackQuery):
    """Статус мультиплеерной игры"""
    lobby_id = int(callback.data.replace("mp_status_", ""))
    
    lobby = db.get_lobby(lobby_id)
    if not lobby:
        await callback.answer("Игра не найдена!", show_alert=True)
        return
    
    players = json.loads(lobby[2])
    
    await callback.answer(
        f"🎮 Статус игры:\nИгроков: {len(players)}\nЛобби: #{lobby_id}",
        show_alert=True
    )

@multiplayer_router.callback_query(F.data == "create_lobby")
async def create_lobby_menu(callback: CallbackQuery):
    """Меню создания лобби"""
    user_id = callback.from_user.id
    
    user_lobby = db.get_user_lobby(user_id)
    if user_lobby:
        lobby_id = user_lobby[0]
        players = json.loads(user_lobby[2])
        await show_lobby_info(callback, lobby_id, players)
        await callback.answer("Ты уже в лобби!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🎪 Создание лобби\n\n"
        "Выбери максимальное количество игроков:",
        reply_markup=keyboards.lobby_players_count()
    )

@multiplayer_router.callback_query(F.data.startswith("create_lobby_"))
async def create_lobby(callback: CallbackQuery):
    """Создание лобби"""
    max_players = int(callback.data.replace("create_lobby_", ""))
    user_id = callback.from_user.id
    
    user_lobby = db.get_user_lobby(user_id)
    if user_lobby:
        lobby_id = user_lobby[0]
        players = json.loads(user_lobby[2])
        await show_lobby_info(callback, lobby_id, players)
        await callback.answer("Ты уже в лобби!", show_alert=True)
        return
    
    lobby_id = db.create_lobby(user_id, max_players)
    
    await callback.message.edit_text(
        f"🎪 Лобби создано!\n\n"
        f"🔢 ID лобби: {lobby_id}\n"
        f"👥 Макс. игроков: {max_players}\n"
        f"⏳ Ожидание игроков...\n\n"
        f"Другие игроки могут присоединиться по ID: {lobby_id}",
        reply_markup=keyboards.lobby_management(lobby_id, True)
    )

@multiplayer_router.callback_query(F.data == "join_lobby")
async def join_lobby_menu(callback: CallbackQuery, state: FSMContext):
    """Меню присоединения к лобби"""
    user_id = callback.from_user.id
    
    user_lobby = db.get_user_lobby(user_id)
    if user_lobby:
        lobby_id = user_lobby[0]
        players = json.loads(user_lobby[2])
        await show_lobby_info(callback, lobby_id, players)
        await callback.answer("Ты уже в лобби!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🔗 Присоединение к лобби\n\n"
        "Введи ID лобби (число):",
        reply_markup=keyboards.back_to_multiplayer()
    )
    await state.set_state(MultiplayerStates.joining_lobby)

@multiplayer_router.message(MultiplayerStates.joining_lobby)
async def process_join_lobby(message: Message, state: FSMContext):
    """Обработка присоединения к лобби"""
    try:
        lobby_id = int(message.text)
        user_id = message.from_user.id
        
        success, result = db.join_lobby(lobby_id, user_id)
        
        if success:
            lobby = db.get_lobby(lobby_id)
            players = json.loads(lobby[2])
            await show_lobby_info(message, lobby_id, players)
        else:
            await message.answer(f"❌ {result}\n\nПопробуй другой ID:", reply_markup=keyboards.back_to_multiplayer())
            
    except ValueError:
        await message.answer("❌ Введи корректный ID лобби (число)\n\nПопробуй еще раз:", reply_markup=keyboards.back_to_multiplayer())
    
    await state.clear()

@multiplayer_router.callback_query(F.data == "list_lobbies")
async def list_lobbies(callback: CallbackQuery):
    """Список активных лобби"""
    user_id = callback.from_user.id
    
    user_lobby = db.get_user_lobby(user_id)
    if user_lobby:
        lobby_id = user_lobby[0]
        players = json.loads(user_lobby[2])
        await show_lobby_info(callback, lobby_id, players)
        await callback.answer("Ты уже в лобби!", show_alert=True)
        return
    
    lobbies = db.get_active_lobbies()
    
    if not lobbies:
        await callback.message.edit_text(
            "📋 Активные лобби\n\n"
            "😔 Сейчас нет активных лобби\n"
            "Создай своё или проверь позже!",
            reply_markup=keyboards.back_to_multiplayer()
        )
        return
    
    text = "📋 Активные лобби:\n\n"
    for lobby in lobbies:
        lobby_id, creator_id, players_data, status = lobby
        players = json.loads(players_data)
        text += f"🎪 Лобби #{lobby_id}\n"
        text += f"👥 Игроков: {len(players)}/5\n"
        text += f"🆔 ID для присоединения: {lobby_id}\n\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboards.lobbies_list(lobbies)
    )

@multiplayer_router.callback_query(F.data.startswith("join_lobby_"))
async def quick_join_lobby(callback: CallbackQuery):
    """Быстрое присоединение к лобби из списка"""
    lobby_id = int(callback.data.replace("join_lobby_", ""))
    user_id = callback.from_user.id
    
    user_lobby = db.get_user_lobby(user_id)
    if user_lobby:
        existing_lobby_id = user_lobby[0]
        players = json.loads(user_lobby[2])
        await show_lobby_info(callback, existing_lobby_id, players)
        await callback.answer("Ты уже в лобби!", show_alert=True)
        return
    
    success, result = db.join_lobby(lobby_id, user_id)
    
    if success:
        lobby = db.get_lobby(lobby_id)
        players = json.loads(lobby[2])
        await show_lobby_info(callback, lobby_id, players)
    else:
        await callback.answer(f"❌ {result}", show_alert=True)

@multiplayer_router.callback_query(F.data.startswith("leave_lobby_"))
async def leave_lobby(callback: CallbackQuery):
    """Выйти из лобби"""
    lobby_id = int(callback.data.replace("leave_lobby_", ""))
    user_id= callback.from_user.id
    
    lobby = db.get_lobby(lobby_id)
    if not lobby:
        await callback.answer("Лобби не найдено!", show_alert=True)
        return
    
    players = json.loads(lobby[2])
    
    if user_id not in players:
        await callback.answer("Ты не в этом лобби!", show_alert=True)
        return
    
    players.remove(user_id)
    
    cursor = db.conn.cursor()
    if players:
        cursor.execute('UPDATE multiplayer_lobbies SET players = ? WHERE lobby_id = ?', 
                      (json.dumps(players), lobby_id))
    else:
        cursor.execute('DELETE FROM multiplayer_lobbies WHERE lobby_id = ?', (lobby_id,))
    
    db.conn.commit()
    
    await callback.message.edit_text(
        "✅ Ты вышел из лобби",
        reply_markup=keyboards.multiplayer_main()
    )

@multiplayer_router.callback_query(F.data.startswith("refresh_lobby_"))
async def refresh_lobby(callback: CallbackQuery):
    """Обновить лобби"""
    lobby_id = int(callback.data.replace("refresh_lobby_", ""))
    user_id = callback.from_user.id
    
    lobby = db.get_lobby(lobby_id)
    if not lobby:
        await callback.answer("Лобби не найдено!", show_alert=True)
        return
    
    players = json.loads(lobby[2])
    
    if user_id not in players:
        await callback.answer("Ты не в этом лобби!", show_alert=True)
        return
    
    await show_lobby_info(callback, lobby_id, players)

@multiplayer_router.callback_query(F.data == "back_to_multiplayer")
async def back_to_multiplayer(callback: CallbackQuery):
    """Возврат в мультиплеер"""
    user_id = callback.from_user.id
    
    # Очищаем пользователя из лобби
    db.delete_user_from_all_lobbies(user_id)
    
    await callback.message.edit_text(
        "👥 Мультиплеер\n\nВыбери действие:",
        reply_markup=keyboards.multiplayer_main()
    )