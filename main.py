import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeDefault

from config import config
from handlers.menu import menu_router
from handlers.game import game_router
from handlers.shop import shop_router
from handlers.multiplayer import multiplayer_router

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

dp.include_router(menu_router)
dp.include_router(game_router)
dp.include_router(shop_router)
dp.include_router(multiplayer_router)

async def set_bot_commands():
    """Установка меню команд бота"""
    commands = [
        BotCommand(command="/start", description="🎮 Главное меню"),
        BotCommand(command="/game", description="🎮 Начать игру"),
        BotCommand(command="/multiplayer", description="👥 Мультиплеер"),
        BotCommand(command="/shop", description="🛍️ Магазин"),
        BotCommand(command="/profile", description="📊 Профиль"),
        BotCommand(command="/rules", description="ℹ️ Правила игры"),
        BotCommand(command="/daily", description="🎁 Ежедневная награда"),
        BotCommand(command="/help", description="🆘 Помощь")
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())

async def main():
    logging.info("🚀 Бот запускается...")
    
    # Устанавливаем меню команд
    await set_bot_commands()
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())