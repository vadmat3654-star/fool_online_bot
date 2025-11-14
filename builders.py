from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                          InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import InlineKeyboardBuilder

class MenuKeyboards:
    @staticmethod
    def main_menu():
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🎮 Начать игру")],
                [KeyboardButton(text="👥 Мультиплеер"), KeyboardButton(text="🏆 Турниры")],
                [KeyboardButton(text="🛍️ Магазин"), KeyboardButton(text="📊 Профиль")],
                [KeyboardButton(text="ℹ️ Правила"), KeyboardButton(text="🎁 Ежедневная награда")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        )
    
    @staticmethod
    def game_mode():
        builder = InlineKeyboardBuilder()
        builder.button(text="🤖 Игра с ботом", callback_data="game_bot")
        builder.button(text="👥 Мультиплеер (2-5 игроков)", callback_data="game_multiplayer") 
        builder.button(text="🏆 Турнирный режим", callback_data="game_tournament")
        builder.button(text="⬅️ Назад", callback_data="back_to_menu")
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def difficulty():
        builder = InlineKeyboardBuilder()
        builder.button(text="😊 Легкий бот", callback_data="diff_easy")
        builder.button(text="😐 Средний бот", callback_data="diff_medium")
        builder.button(text="😡 Сложный бот", callback_data="diff_hard")
        builder.button(text="⬅️ Назад", callback_data="back_to_game_mode")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def shop_categories():
        builder = InlineKeyboardBuilder()
        builder.button(text="🎨 Скины для карт", callback_data="shop_skins")
        builder.button(text="🎁 Боксы со скинами", callback_data="shop_boxes")
        builder.button(text="💰 Купить звезды", callback_data="shop_currency")
        builder.button(text="📦 Мой инвентарь", callback_data="my_inventory")
        builder.button(text="⬅️ Назад", callback_data="back_to_menu")
        builder.adjust(2)
        return builder.as_markup()
    
    @staticmethod
    def shop_skins_list(skins):
        builder = InlineKeyboardBuilder()
        for skin in skins:
            skin_id, name, _, price, _, _, _ = skin
            builder.button(text=f"{name} - {price}⭐", callback_data=f"buy_{skin_id}")
        builder.button(text="⬅️ Назад", callback_data="back_to_shop")
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def shop_boxes_list(boxes):
        builder = InlineKeyboardBuilder()
        for box in boxes:
            box_id, name, _, price, _, _, _ = box
            builder.button(text=f"{name} - {price}⭐", callback_data=f"buy_{box_id}")
        builder.button(text="⬅️ Назад", callback_data="back_to_shop")
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def shop_after_purchase():
        builder = InlineKeyboardBuilder()
        builder.button(text="🛍️ Продолжить покупки", callback_data="back_to_shop")
        builder.button(text="📊 Профиль", callback_data="back_to_menu")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def game_cards(cards):
        builder = InlineKeyboardBuilder()
        for i, card in enumerate(cards):
            builder.button(text=str(card), callback_data=f"play_{i}")
        builder.button(text="🏳️ Сдаться", callback_data="surrender")
        builder.button(text="⏭️ Пропустить ход", callback_data="skip_turn")
        builder.adjust(3)
        return builder.as_markup()

    @staticmethod
    def game_cards_with_take(cards):
        builder = InlineKeyboardBuilder()
        for i, card in enumerate(cards):
            builder.button(text=str(card), callback_data=f"play_{i}")
        builder.button(text="🎴 Взять карты", callback_data="take_cards")
        builder.button(text="🏳️ Сдаться", callback_data="surrender")
        builder.adjust(3)
        return builder.as_markup()

    @staticmethod
    def get_game_keyboard(game):
        """Динамическая клавиатура в зависимости от состояния игры"""
        builder = InlineKeyboardBuilder()
        
        # Кнопки карт
        for i, card in enumerate(game.players[0]):
            builder.button(text=str(card), callback_data=f"play_{i}")
        
        # Специальные кнопки в зависимости от действия
        if game.current_action == "defend":
            builder.button(text="🎴 Взять карты", callback_data="take_cards")
        elif game.current_action == "add":
            builder.button(text="⏹️ Пасовать", callback_data="pass_turn")
        
        builder.button(text="🏳️ Сдаться", callback_data="surrender")
        builder.adjust(3)
        return builder.as_markup()

    @staticmethod
    def back_to_menu():
        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️ В главное меню", callback_data="back_to_menu")
        return builder.as_markup()

    @staticmethod
    def multiplayer_main():
        builder = InlineKeyboardBuilder()
        builder.button(text="🎪 Создать лобби", callback_data="create_lobby")
        builder.button(text="🔗 Присоединиться по ID", callback_data="join_lobby")
        builder.button(text="📋 Список лобби", callback_data="list_lobbies")
        builder.button(text="🆘 Выйти из всех лобби", callback_data="force_leave_lobby")
        builder.button(text="⬅️ Назад", callback_data="back_to_menu")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def lobby_players_count():
        builder = InlineKeyboardBuilder()
        builder.button(text="2 игрока", callback_data="create_lobby_2")
        builder.button(text="3 игрока", callback_data="create_lobby_3")
        builder.button(text="4 игрока", callback_data="create_lobby_4")
        builder.button(text="5 игроков", callback_data="create_lobby_5")
        builder.button(text="⬅️ Назад", callback_data="back_to_multiplayer")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def lobby_management(lobby_id: int, is_creator: bool):
        builder = InlineKeyboardBuilder()
        
        if is_creator:
            builder.button(text="🎮 Начать игру", callback_data=f"start_real_game_{lobby_id}")
            builder.button(text="🗑️ Удалить лобби", callback_data=f"delete_lobby_{lobby_id}")
        
        builder.button(text="🔄 Обновить", callback_data=f"refresh_lobby_{lobby_id}")
        builder.button(text="🚪 Выйти", callback_data=f"leave_lobby_{lobby_id}")
        builder.button(text="🎪 Другие лобби", callback_data="list_lobbies")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def refresh_lobby(lobby_id: int):
        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 Обновить", callback_data=f"refresh_lobby_{lobby_id}")
        builder.button(text="🚪 Выйти", callback_data=f"leave_lobby_{lobby_id}")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def back_to_multiplayer():
        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️ В мультиплеер", callback_data="back_to_multiplayer")
        return builder.as_markup()

    @staticmethod
    def lobbies_list(lobbies):
        builder = InlineKeyboardBuilder()
        for lobby in lobbies:
            lobby_id = lobby[0]
            builder.button(text=f"🎪 Присоединиться к #{lobby_id}", callback_data=f"join_lobby_{lobby_id}")
        builder.button(text="🔄 Обновить", callback_data="list_lobbies")
        builder.button(text="⬅️ Назад", callback_data="back_to_multiplayer")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def inventory_actions(skins, boxes):
        builder = InlineKeyboardBuilder()
        
        for box_type, box_name, quantity in boxes:
            builder.button(text=f"🎁 Открыть {box_name}", callback_data=f"open_box_{box_name}")
        
        for skin in skins:
            builder.button(text=f"🎨 Надеть {skin}", callback_data=f"equip_skin_{skin}")
        
        builder.button(text="🛍️ В магазин", callback_data="back_to_shop")
        builder.button(text="⬅️ Назад", callback_data="back_to_menu")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def after_box_open():
        builder = InlineKeyboardBuilder()
        builder.button(text="📦 В инвентарь", callback_data="back_to_inventory")
        builder.button(text="🛍️ В магазин", callback_data="back_to_shop")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def back_to_inventory():
        builder = InlineKeyboardBuilder()
        builder.button(text="📦 В инвентарь", callback_data="back_to_inventory")
        builder.button(text="🛍️ В магазин", callback_data="back_to_shop")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def force_leave_button():
        builder = InlineKeyboardBuilder()
        builder.button(text="🆘 Выйти из всех лобби", callback_data="force_leave_lobby")
        builder.button(text="👥 В мультиплеер", callback_data="back_to_multiplayer")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def multiplayer_game_interface(lobby_id: int):
        builder = InlineKeyboardBuilder()
        builder.button(text="🎴 Сделать ход", callback_data=f"mp_play_{lobby_id}")
        builder.button(text="🏳️ Сдаться", callback_data=f"mp_surrender_{lobby_id}")
        builder.button(text="📊 Статус игры", callback_data=f"mp_status_{lobby_id}")
        builder.adjust(1)
        return builder.as_markup()

keyboards = MenuKeyboards()