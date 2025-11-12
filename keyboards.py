from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Играть", callback_data="play_menu")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
         InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="🏆 Турниры", callback_data="tournaments"),
         InlineKeyboardButton(text="⭐ Купить звёзды", callback_data="buy_stars")],
        [InlineKeyboardButton(text="🎁 Ежедневная награда", callback_data="daily_reward")],
        [InlineKeyboardButton(text="📚 Правила", callback_data="rules")]
    ])

def play_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Игра с ботом", callback_data="bot_game")],
        [InlineKeyboardButton(text="👥 Мультиплеер", callback_data="multiplayer")],
        [InlineKeyboardButton(text="🎯 Турнир", callback_data="tournament_game")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])

def bot_difficulty():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="😊 Легкий", callback_data="bot_easy")],
        [InlineKeyboardButton(text="😐 Средний", callback_data="bot_medium")],
        [InlineKeyboardButton(text="😈 Сложный", callback_data="bot_hard")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="play_menu")]
    ])

def multiplayer_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 2 игрока", callback_data="mp_2")],
        [InlineKeyboardButton(text="👥👥 3 игрока", callback_data="mp_3")],
        [InlineKeyboardButton(text="👥👥👥 4 игрока", callback_data="mp_4")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="play_menu")]
    ])

def cards_keyboard(cards, action="attack"):
    """Клавиатура для выбора карт"""
    keyboard = []
    for card in cards:
        keyboard.append([InlineKeyboardButton(
            text=str(card), 
            callback_data=f"{action}_{str(card)}"
        )])
    keyboard.append([InlineKeyboardButton(text="⏹️ Закончить ход", callback_data="end_turn")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def skins_keyboard(available_skins, current_skin):
    """Клавиатура для выбора скинов"""
    keyboard = []
    for skin_id, skin_data in config.SKINS.items():
        if skin_id in available_skins:
            status = "✅" if skin_id == current_skin else "⭐"
            price = f" - {skin_data['price']} звёзд" if skin_data['price'] > 0 else ""
            keyboard.append([InlineKeyboardButton(
                text=f"{status} {skin_data['name']}{price}",
                callback_data=f"select_skin_{skin_id}"
            )])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="profile")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def stars_keyboard():
    """Клавиатура для покупки звёзд"""
    keyboard = []
    for package, amount in config.STAR_PACKAGES.items():
        keyboard.append([InlineKeyboardButton(
            text=f"⭐ {amount} звёзд - {amount} руб",
            callback_data=f"buy_{package}"
        )])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)