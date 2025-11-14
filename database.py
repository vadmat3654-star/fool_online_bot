import sqlite3
import json
import random
from datetime import datetime, timedelta
from config import config

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('fool_game.db', check_same_thread=False)
        self.clean_duplicates()
        self.create_tables()
    
    def clean_duplicates(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            DELETE FROM shop_items 
            WHERE id NOT IN (
                SELECT MIN(id) 
                FROM shop_items 
                GROUP BY name, type, price
            )
        ''')
        self.conn.commit()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                stars INTEGER DEFAULT 100,
                games_played INTEGER DEFAULT 0,
                games_won INTEGER DEFAULT 0,
                registration_date TEXT DEFAULT CURRENT_TIMESTAMP,
                current_skin TEXT DEFAULT 'classic',
                daily_reward_date TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_skins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                skin_name TEXT,
                purchased_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_games (
                game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_type TEXT,
                players TEXT,
                game_state TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS multiplayer_lobbies (
                lobby_id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER,
                players TEXT,
                status TEXT DEFAULT 'waiting',
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shop_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                type TEXT,
                price INTEGER,
                rarity TEXT,
                effect TEXT,
                image TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_type TEXT,
                item_name TEXT,
                quantity INTEGER DEFAULT 1,
                obtained_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                amount INTEGER,
                description TEXT,
                date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        self.initialize_shop()
        self.conn.commit()
    
    def initialize_shop(self):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM shop_items')
        
        skins = [
            ('Классический', 'skin', 0, 'common', 'Стандартный дизайн карт', '🎴'),
            ('Золотой', 'skin', 500, 'rare', 'Золотые карты с анимацией', '🟡'),
            ('Неоновый', 'skin', 1000, 'epic', 'Неоновое свечение карт', '💠'),
            ('Космический', 'skin', 2000, 'legendary', 'Анимированные космические карты', '🚀'),
            ('Вампирский', 'skin', 1500, 'epic', 'Темные карты с кровавым оттенком', '🦇')
        ]
        
        boxes = [
            ('Обычный бокс', 'box', 100, 'common', 'Шанс получить обычный или редкий скин', '📦'),
            ('Эпический бокс', 'box', 500, 'epic', 'Шанс получить эпический или легендарный скин', '🎁'),
            ('Легендарный бокс', 'box', 1000, 'legendary', 'Гарантированный легендарный скин', '💎')
        ]
        
        for item in skins + boxes:
            cursor.execute('''
                INSERT INTO shop_items (name, type, price, rarity, effect, image)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', item)
        
        self.conn.commit()

    def get_user(self, user_id: int):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()
    
    def create_user(self, user_id: int, username: str, full_name: str):
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)',
            (user_id, username, full_name)
        )
        
        cursor.execute(
            'INSERT OR IGNORE INTO user_skins (user_id, skin_name) VALUES (?, ?)',
            (user_id, 'classic')
        )
        
        self.conn.commit()
        return self.get_user(user_id)
    
    def update_user_stats(self, user_id: int, won: bool = False):
        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE users SET games_played = games_played + 1 WHERE user_id = ?',
            (user_id,)
        )
        if won:
            cursor.execute(
                'UPDATE users SET games_won = games_won + 1, stars = stars + 10 WHERE user_id = ?',
                (user_id,)
            )
        self.conn.commit()

    def get_shop_items(self, item_type: str = None):
        cursor = self.conn.cursor()
        if item_type:
            cursor.execute('SELECT * FROM shop_items WHERE type = ? ORDER BY price', (item_type,))
        else:
            cursor.execute('SELECT * FROM shop_items ORDER BY type, price')
        return cursor.fetchall()
    
    def get_user_stars(self, user_id: int):
        cursor = self.conn.cursor()
        cursor.execute('SELECT stars FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 0
    
    def purchase_item(self, user_id: int, item_id: int):
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT * FROM shop_items WHERE id = ?', (item_id,))
        item = cursor.fetchone()
        
        if not item:
            return False, "Товар не найден"
        
        item_name, item_type, price, rarity, effect, image = item[1], item[2], item[3], item[4], item[5], item[6]
        
        user_stars = self.get_user_stars(user_id)
        if user_stars < price:
            return False, "Недостаточно звезд"
        
        cursor.execute(
            'UPDATE users SET stars = stars - ? WHERE user_id = ?',
            (price, user_id)
        )
        
        if item_type == 'skin':
            cursor.execute(
                'INSERT INTO user_skins (user_id, skin_name) VALUES (?, ?)',
                (user_id, item_name)
            )
        else:
            cursor.execute('SELECT quantity FROM user_inventory WHERE user_id = ? AND item_name = ? AND item_type = ?', 
                          (user_id, item_name, item_type))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute('UPDATE user_inventory SET quantity = quantity + 1 WHERE user_id = ? AND item_name = ? AND item_type = ?', 
                              (user_id, item_name, item_type))
            else:
                cursor.execute(
                    'INSERT INTO user_inventory (user_id, item_type, item_name, quantity) VALUES (?, ?, ?, ?)',
                    (user_id, item_type, item_name, 1)
                )
        
        cursor.execute(
            'INSERT INTO user_transactions (user_id, type, amount, description) VALUES (?, ?, ?, ?)',
            (user_id, 'purchase', -price, f'Покупка: {item_name}')
        )
        
        self.conn.commit()
        return True, f"Успешная покупка: {item_name}"

    def create_lobby(self, creator_id: int, max_players: int = 4):
        cursor = self.conn.cursor()
        players_data = json.dumps([creator_id])
        
        cursor.execute('''
            INSERT INTO multiplayer_lobbies (creator_id, players, status)
            VALUES (?, ?, ?)
        ''', (creator_id, players_data, 'waiting'))
        
        lobby_id = cursor.lastrowid
        self.conn.commit()
        return lobby_id

    def get_lobby(self, lobby_id: int):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM multiplayer_lobbies WHERE lobby_id = ?', (lobby_id,))
        return cursor.fetchone()

    def join_lobby(self, lobby_id: int, user_id: int):
        cursor = self.conn.cursor()
        
        lobby = self.get_lobby(lobby_id)
        if not lobby:
            return False, "Лобби не найдено"
        
        players = json.loads(lobby[2])
        
        if user_id in players:
            return False, "Ты уже в лобби"
        
        if len(players) >= 5:
            return False, "Лобби заполнено"
        
        players.append(user_id)
        
        cursor.execute('''
            UPDATE multiplayer_lobbies 
            SET players = ? 
            WHERE lobby_id = ?
        ''', (json.dumps(players), lobby_id))
        
        self.conn.commit()
        return True, "Успешно присоединился к лобби"

    def get_active_lobbies(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT lobby_id, creator_id, players, status 
            FROM multiplayer_lobbies 
            WHERE status = 'waiting'
            ORDER BY created_date DESC
        ''')
        return cursor.fetchall()

    def start_lobby_game(self, lobby_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE multiplayer_lobbies 
            SET status = 'playing' 
            WHERE lobby_id = ?
        ''', (lobby_id,))
        self.conn.commit()

    def delete_lobby(self, lobby_id: int):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM multiplayer_lobbies WHERE lobby_id = ?', (lobby_id,))
        self.conn.commit()

    def get_user_lobby(self, user_id: int):
        """Получить лобби пользователя - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM multiplayer_lobbies 
            WHERE players LIKE ? AND status = 'waiting'
        ''', (f'%{user_id}%',))
        return cursor.fetchone()

    def delete_user_from_all_lobbies(self, user_id: int):
        """Удалить пользователя из всех лобби - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        cursor = self.conn.cursor()
        
        # Получаем все лобби где есть пользователь
        cursor.execute('SELECT lobby_id, players FROM multiplayer_lobbies WHERE players LIKE ?', (f'%{user_id}%',))
        lobbies = cursor.fetchall()
        
        for lobby in lobbies:
            lobby_id, players_data = lobby
            players = json.loads(players_data)
            
            if user_id in players:
                players.remove(user_id)
                
                if players:  # Если еще остались игроки
                    cursor.execute('UPDATE multiplayer_lobbies SET players = ? WHERE lobby_id = ?', 
                                  (json.dumps(players), lobby_id))
                else:  # Если лобби пустое - удаляем
                    cursor.execute('DELETE FROM multiplayer_lobbies WHERE lobby_id = ?', (lobby_id,))
        
        self.conn.commit()
        return True

    def get_user_inventory(self, user_id: int):
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT skin_name FROM user_skins WHERE user_id = ?', (user_id,))
        skins = [row[0] for row in cursor.fetchall()]
        
        cursor.execute('SELECT item_type, item_name, quantity FROM user_inventory WHERE user_id = ?', (user_id,))
        inventory = cursor.fetchall()
        
        return skins, inventory

    def open_box(self, user_id: int, box_name: str):
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT quantity FROM user_inventory WHERE user_id = ? AND item_name = ? AND item_type = "box"', 
                      (user_id, box_name))
        result = cursor.fetchone()
        
        if not result or result[0] <= 0:
            return False, "У тебя нет такого бокса"
        
        skin_rarities = {
            "Обычный бокс": ["common", "rare"],
            "Эпический бокс": ["rare", "epic"], 
            "Легендарный бокс": ["epic", "legendary"]
        }
        
        if box_name not in skin_rarities:
            return False, "Неизвестный тип бокса"
        
        rarities = skin_rarities[box_name]
        cursor.execute('SELECT name FROM shop_items WHERE type = "skin" AND rarity IN (?, ?) ORDER BY RANDOM() LIMIT 1', 
                      (rarities[0], rarities[1]))
        skin_result = cursor.fetchone()
        
        if not skin_result:
            return False, "Не удалось найти подходящий скин"
        
        skin_name = skin_result[0]
        
        cursor.execute('SELECT 1 FROM user_skins WHERE user_id = ? AND skin_name = ?', (user_id, skin_name))
        if cursor.fetchone():
            return False, f"У тебя уже есть скин {skin_name}"
        
        cursor.execute('INSERT INTO user_skins (user_id, skin_name) VALUES (?, ?)', (user_id, skin_name))
        
        cursor.execute('UPDATE user_inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_name = ? AND item_type = "box"', 
                      (user_id, box_name))
        
        cursor.execute('DELETE FROM user_inventory WHERE user_id = ? AND item_name = ? AND quantity <= 0', 
                      (user_id, box_name))
        
        self.conn.commit()
        return True, f"🎉 Ты получил скин: {skin_name}!"

    def equip_skin(self, user_id: int, skin_name: str):
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT 1 FROM user_skins WHERE user_id = ? AND skin_name = ?', (user_id, skin_name))
        if not cursor.fetchone():
            return False, "У тебя нет этого скина"
        
        cursor.execute('UPDATE users SET current_skin = ? WHERE user_id = ?', (skin_name, user_id))
        self.conn.commit()
        return True, f"🎨 Надет скин: {skin_name}"

    def get_daily_reward(self, user_id: int):
        """Получить ежедневную награду"""
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT daily_reward_date, stars FROM users WHERE user_id = ?', (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            return False, "Пользователь не найден"
        
        last_reward_date = user_data[0]
        current_stars = user_data[1]
        
        now = datetime.now()
        
        if last_reward_date:
            try:
                last_reward = datetime.strptime(last_reward_date, '%Y-%m-%d %H:%M:%S')
                if now - last_reward < timedelta(hours=24):
                    next_reward = last_reward + timedelta(hours=24)
                    time_left = next_reward - now
                    hours_left = int(time_left.total_seconds() // 3600)
                    minutes_left = int((time_left.total_seconds() % 3600) // 60)
                    return False, f"Следующая награда через: {hours_left}ч {minutes_left}м"
            except:
                # Если ошибка парсинга даты, просто выдаем награду
                pass
        
        # Выдаем награду
        reward_amount = 50
        cursor.execute(
            'UPDATE users SET stars = stars + ?, daily_reward_date = ? WHERE user_id =?',
            (reward_amount, now.strftime('%Y-%m-%d %H:%M:%S'), user_id)
        )
        
        cursor.execute(
            'INSERT INTO user_transactions (user_id, type, amount, description) VALUES (?, ?, ?, ?)',
            (user_id, 'daily_reward', reward_amount, 'Ежедневная награда')
        )
        
        self.conn.commit()
        return True, f"🎁 Ты получил {reward_amount} звезд!"

db = Database()