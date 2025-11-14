from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from database import db
from keyboards.builders import MenuKeyboards

menu_router = Router()
keyboards = MenuKeyboards()

# ===== КОМАНДЫ БОТА =====

@menu_router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    if not user:
        db.create_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    
    await message.answer(
        "🎉 Добро пожаловать в Дурак Online! 🃏\n\n"
        "Здесь тебя ждут:\n"
        "• 🤖 Умные боты разных уровней\n"  
        "• 👥 Мультиплеер с друзьями\n"
        "• 🏆 Турниры с призами\n"
        "• 🎨 Уникальные скины и анимации\n"
        "• 🎁 Ежедневные награды\n\n"
        "Выбери действие в меню ниже 👇",
        reply_markup=keyboards.main_menu()
    )
    await state.clear()

@menu_router.message(Command("game"))
async def cmd_game(message: Message):
    """Команда /game - быстрый старт игры"""
    await message.answer(
        "🎯 Выбери режим игры:\n\n"
        "• 🤖 Против бота - играй в любое время\n"
        "• 👥 Мультиплеер - с друзьями (2-5 игроков)\n"  
        "• 🏆 Турниры - соревнуйся за призы",
        reply_markup=keyboards.game_mode()
    )

@menu_router.message(Command("multiplayer"))
async def cmd_multiplayer(message: Message):
    """Команда /multiplayer - быстрый вход в мультиплеер"""
    from database import db
    
    # Принудительно очищаем пользователя из лобби
    db.delete_user_from_all_lobbies(message.from_user.id)
    
    await message.answer(
        "👥 Мультиплеер - РАБОТАЕТ! 🎮\n\n"
        "Создай лобби и пригласи друзей!\n\n"
        "Выбери действие:",
        reply_markup=keyboards.multiplayer_main()
    )

@menu_router.message(Command("shop"))
async def cmd_shop(message: Message):
    """Команда /shop - быстрый вход в магазин"""
    user_stars = db.get_user_stars(message.from_user.id)
    
    await message.answer(
        f"🛍️ Магазин скинов\n\n"
        f"💰 Твой баланс: {user_stars} звезд\n\n"
        f"Выбери категорию:",
        reply_markup=keyboards.shop_categories()
    )

@menu_router.message(Command("profile"))
async def cmd_profile(message: Message):
    """Команда /profile - быстрый просмотр профиля"""
    user = db.get_user(message.from_user.id)
    if user:
        win_rate = (user[5] / user[4] * 100) if user[4] > 0 else 0
        
        await message.answer(
            f"👤 Твой профиль\n\n"
            f"🎮 Игр сыграно: {user[4]}\n"
            f"🏅 Побед: {user[5]}\n"
            f"📈 Винрейт: {win_rate:.1f}%\n"
            f"💰 Звёзд: {user[3]}\n"
            f"🎨 Скин: {user[7]}"
        )

@menu_router.message(Command("rules"))
async def cmd_rules(message: Message):
    """Команда /rules - правила игры"""
    await message.answer(
        "📖 Правила игры в Дурака\n\n"
        "🎯 Цель игры:\n"
        "• Первым избавиться от всех карт\n\n"
        "🃏 Ход игры:\n"  
        "• Игроки получают по 6 карт\n"
        "• Первый ход делает игрок с младшим козырем\n"
        "• Можно подкидывать карты того же достоинства\n"
        "• Защищающийся должен побить все карты\n\n"
        "🏆 Победа:\n"
        "• Кто первым остался без карт - тот победил!\n\n"
        "Готов испытать удачу? 😉"
    )

@menu_router.message(Command("daily"))
async def cmd_daily(message: Message):
    """Команда /daily - ежедневная награда"""
    success, result = db.get_daily_reward(message.from_user.id)
    
    if success:
        user_stars = db.get_user_stars(message.from_user.id)
        await message.answer(
            f"🎁 Ежедневная награда\n\n"
            f"✅ {result}\n\n"
            f"💰 Теперь у тебя: {user_stars} звезд!\n\n"
            f"Возвращайся завтра за новой наградой! 🎉"
        )
    else:
        await message.answer(
            f"🎁 Ежедневная награда\n\n"
            f"⏳ {result}\n\n"
            f"Заходи позже! 😊"
        )

@menu_router.message(Command("help"))
async def cmd_help(message: Message):
    """Команда /help - помощь"""
    await message.answer(
        "🆘 Помощь по боту Дурак Online\n\n"
        "📋 Доступные команды:\n"
        "• /start - главное меню\n"
        "• /game - начать игру\n" 
        "• /multiplayer - мультиплеер\n"
        "• /shop - магазин скинов\n"
        "• /profile - твой профиль\n"
        "• /rules - правила игры\n"
        "• /daily - ежедневная награда\n"
        "• /help - эта справка\n\n"
        "🎮 Игровые режимы:\n"
        "• 🤖 Против бота - тренируйся\n"
        "• 👥 Мультиплеер - с друзьями\n"
        "• 🏆 Турниры - соревнуйся\n\n"
        "🛍️ Экономика:\n"
        "• Зарабатывай звёзды за победы\n"
        "• Покупай скины и боксы\n"
        "• Открывай боксы и получай редкие скины\n\n"
        "❓ Проблемы?\n"
        "Если что-то не работает - используй кнопку 'Выйти из всех лобби' в мультиплеере"
    )

# ===== ОСНОВНЫЕ ОБРАБОТЧИКИ МЕНЮ (остаются без изменений) =====

@menu_router.message(F.text == "🎮 Начать игру")
async def start_game_menu(message: Message):
    await message.answer(
        "🎯 Выбери режим игры:\n\n"
        "• 🤖 Против бота - играй в любое время\n"
        "• 👥 Мультиплеер - с друзьями (2-5 игроков)\n"  
        "• 🏆 Турниры - соревнуйся за призы",
        reply_markup=keyboards.game_mode()
    )

@menu_router.message(F.text == "👥 Мультиплеер")
async def multiplayer_menu(message: Message):
    """Меню мультиплеера с принудительной очисткой"""
    from database import db
    
    # Принудительно очищаем пользователя из лобби
    db.delete_user_from_all_lobbies(message.from_user.id)
    
    await message.answer(
        "👥 Мультиплеер\n\n"
        "Играй с друзьями в реальном времени!\n\n"
        "• 🎪 Создать комнату\n"
        "• 📋 Список открытых игр\n"
        "• 🔗 Присоединиться по коду\n\n"
        "✅ Все лобби очищены, можно создавать новое!",
        reply_markup=keyboards.multiplayer_main()
    )

@menu_router.message(F.text == "🏆 Турниры")
async def tournaments_menu(message: Message):
    await message.answer(
        "🏆 Турниры\n\n"
        "Соревнуйся за звание лучшего игрока!\n\n"
        "• 🎯 Активные турниры\n"
        "• 📊 Мои результаты\n"
        "• 🏅 Создать турнир\n\n"
        "Система турниров в разработке!"
    )

@menu_router.message(F.text == "🛍️ Магазин")
async def shop_menu(message: Message):
    user_stars = db.get_user_stars(message.from_user.id)
    
    await message.answer(
        f"🛍️ Магазин скинов\n\n"
        f"💰 Твой баланс: {user_stars} звезд\n\n"
        f"Выбери категорию:",
        reply_markup=keyboards.shop_categories()
    )

@menu_router.message(F.text == "📊 Профиль")
async def show_profile(message: Message):
    user = db.get_user(message.from_user.id)
    if user:
        win_rate = (user[5] / user[4] * 100) if user[4] > 0 else 0
        
        await message.answer(
            f"👤 Твой профиль\n\n"
            f"🎮 Игр сыграно: {user[4]}\n"
            f"🏅 Побед: {user[5]}\n"
            f"📈 Винрейт: {win_rate:.1f}%\n"
            f"💰 Звёзд: {user[3]}\n"
            f"🎨 Скин: {user[7]}"
        )

@menu_router.message(F.text == "ℹ️ Правила")
async def show_rules(message: Message):
    await message.answer(
        "📖 Правила игры в Дурака\n\n"
        "🎯 Цель игры:\n"
        "• Первым избавиться от всех карт\n\n"
        "🃏 Ход игры:\n"  
        "• Игроки получают по 6 карт\n"
        "• Первый ход делает игрок с младшим козырем\n"
        "• Можно подкидывать карты того же достоинства\n"
        "• Защищающийся должен побить все карты\n\n"
        "🏆 Победа:\n"
        "• Кто первым остался без карт - тот победил!\n\n"
        "Готов испытать удачу? 😉"
    )

@menu_router.message(F.text == "🎁 Ежедневная награда")
async def daily_reward(message: Message):
    success, result = db.get_daily_reward(message.from_user.id)
    
    if success:
        user_stars = db.get_user_stars(message.from_user.id)
        await message.answer(
            f"🎁 Ежедневная награда\n\n"
            f"✅ {result}\n\n"
            f"💰 Теперь у тебя: {user_stars} звезд!\n\n"
            f"Возвращайся завтра за новой наградой! 🎉"
        )
    else:
        await message.answer(
            f"🎁 Ежедневная награда\n\n"
            f"⏳ {result}\n\n"
            f"Заходи позже! 😊"
        )

# ===== CALLBACK ОБРАБОТЧИКИ МЕНЮ =====

@menu_router.callback_query(F.data == "game_bot")
async def select_bot_game(callback: CallbackQuery):
    await callback.message.edit_text(
        "🤖 Выбери сложность бота:\n\n"
        "• 😊 Легкий - для новичков\n"
        "• 😐 Средний - интересный вызов\n"  
        "• 😡 Сложный - для профи",
        reply_markup=keyboards.difficulty()
    )

@menu_router.callback_query(F.data == "back_to_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🎉 Дурак Online 🃏\n\n"
        "Выбери действие в меню ниже 👇",
        reply_markup=keyboards.main_menu()
    )

@menu_router.callback_query(F.data == "back_to_game_mode")
async def back_to_game_mode(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎯 Выбери режим игры:\n\n"
        "• 🤖 Против бота - играй в любое время\n"
        "• 👥 Мультиплеер - с друзьями (2-5 игроков)\n"  
        "• 🏆 Турниры - соревнуйся за призы",
        reply_markup=keyboards.game_mode()
    )

@menu_router.callback_query(F.data == "back_to_multiplayer")
async def back_to_multiplayer(callback: CallbackQuery):
    from database import db
    db.delete_user_from_all_lobbies(callback.from_user.id)
    
    await callback.message.edit_text(
        "👥 Мультиплеер\n\nВыбери действие:",
        reply_markup=keyboards.multiplayer_main()
    )

@menu_router.callback_query(F.data == "back_to_shop")
async def back_to_shop(callback: CallbackQuery):
    user_stars = db.get_user_stars(callback.from_user.id)
    
    await callback.message.edit_text(
        f"🛍️ Магазин скинов\n\n"
        f"💰 Твой баланс: {user_stars} звезд\n\n"
        f"Выбери категорию:",
        reply_markup=keyboards.shop_categories()
    )