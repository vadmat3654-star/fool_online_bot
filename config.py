import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("8525915886:AAEMqKR9PVNWbRm9jqOhuLGDyBWrHqwXtfQ")

# Настройки игры
MAX_PLAYERS = 4
MOVE_TIMEOUT = 120  # секунды
START_STARS = 100

# Скины и цены
SKINS = {
    "default": {"name": "Стандартный", "price": 0},
    "gold": {"name": "Золотой", "price": 500},
    "demon": {"name": "Демонический", "price": 1000},
    "anime": {"name": "Аниме", "price": 1500},
}

# Пакеты звёзд
STAR_PACKAGES = {
    "100": 100,
    "250": 250, 
    "500": 500,
    "1000": 1000
}