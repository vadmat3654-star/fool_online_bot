import random
from typing import List, Dict, Tuple, Optional

class Card:
    def __init__(self, suit: str, rank: str):
        self.suit = suit
        self.rank = rank
        
    def __str__(self):
        return f"{self.rank}{self.suit}"
    
    def __repr__(self):
        return self.__str__()
    
    def can_beat(self, other, trump_suit: str) -> bool:
        """Может ли эта карта побить другую"""
        if self.suit == other.suit:
            return self.card_value() > other.card_value()
        elif self.suit == trump_suit and other.suit != trump_suit:
            return True
        return False
    
    def card_value(self) -> int:
        values = {'6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        return values.get(self.rank, 0)

class FoolGame:
    def __init__(self, difficulty: str = "easy"):
        self.difficulty = difficulty
        self.deck = self.create_deck()
        self.players = {0: [], 1: []}  # 0 - игрок, 1 - бот
        self.trump = None
        self.attacker = 0  # кто атакует в этом раунде
        self.defender = 1  # кто защищается
        self.table = []    # карты на столе: [атака1, защита1, атака2, защита2...]
        self.game_over = False
        self.winner = None
        self.round_over = False
        self.current_action = "attack"  # attack, defend, add
        
    def create_deck(self) -> List[Card]:
        suits = ['♠', '♥', '♦', '♣']
        ranks = ['6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = [Card(suit, rank) for suit in suits for rank in ranks]
        random.shuffle(deck)
        return deck
    
    def deal_cards(self):
        """Начальная раздача карт"""
        for i in range(2):
            self.draw_cards(i, 6)
        
        if self.deck:
            self.trump = self.deck[-1]
        else:
            self.trump = Card('♠', '6')
    
    def draw_cards(self, player_index: int, count: int):
        """Добор карт игроку"""
        cards_to_draw = min(count, len(self.deck))
        if cards_to_draw > 0:
            self.players[player_index].extend(self.deck[:cards_to_draw])
            self.deck = self.deck[cards_to_draw:]
            # Сортируем карты для удобства
            self.players[player_index].sort(key=lambda x: (x.suit != self.trump.suit, x.card_value()))
    
    def get_game_state(self) -> str:
        player_hand = ' '.join(str(card) for card in self.players[0])
        bot_cards_count = len(self.players[1])
        
        state = (
            f"🎮 Твои карты: {player_hand}\n"
            f"🤖 Карт у бота: {bot_cards_count}\n"
            f"🎯 Козырь: {self.trump}\n"
            f"📊 Карт в колоде: {len(self.deck)}\n"
        )
        
        if self.table:
            table_text = "🎪 На столе:\n"
            for i in range(0, len(self.table), 2):
                attack_card = self.table[i]
                defend_card = self.table[i+1] if i+1 < len(self.table) else None
                if defend_card:
                    table_text += f"  {attack_card} → {defend_card}\n"
                else:
                    table_text += f"  {attack_card} → ?\n"
            state += table_text
        
        if self.current_action == "attack":
            state += f"\n📝 Твой ход: Атака"
        elif self.current_action == "defend":
            state += f"\n📝 Твой ход: Защита"
        elif self.current_action == "add":
            state += f"\n📝 Твой ход: Подкинуть карты"
        
        return state
    
    def can_add_card(self, card: Card) -> bool:
        """Можно ли подкинуть эту карту"""
        if not self.table:
            return False
        
        # Можно подкидывать карты того же достоинства, что уже есть на столе
        table_ranks = {c.rank for c in self.table}
        return card.rank in table_ranks
    
    def player_attack(self, card_index: int) -> str:
        """Игрок атакует картой"""
        if card_index < 0 or card_index >= len(self.players[0]):
            return "Невернаякарта"
        
        if self.current_action != "attack" and self.current_action != "add":
            return "Сейчас нельзя атаковать"
        
        card = self.players[0][card_index]
        
        # Первая атака - любой картой, подкидывание - только совпадающей по достоинству
        if self.table and not self.can_add_card(card):
            return "Можно подкидывать только карты того же достоинства, что на столе"
        
        self.players[0].pop(card_index)
        self.table.append(card)
        
        # После атаки переходим в защиту
        self.current_action = "defend"
        
        return f"Ты атаковал картой: {card}"
    
    def player_defend(self, card_index: int) -> str:
        """Игрок защищается картой"""
        if card_index < 0 or card_index >= len(self.players[0]):
            return "Неверная карта"
        
        if self.current_action != "defend":
            return "Сейчас не защита"
        
        if len(self.table) % 2 != 1:  # Должна быть нечетная карта для отбивания
            return "Нет карты для отбивания"
        
        card = self.players[0][card_index]
        attack_card = self.table[-1]
        
        if card.can_beat(attack_card, self.trump.suit):
            self.players[0].pop(card_index)
            self.table.append(card)
            
            # Проверяем, может ли защищающийся еще подкинуть
            if len(self.players[self.attacker]) > 0 and len(self.table) < 12:  # максимум 6 пар
                self.current_action = "add"
                return f"Ты отбился картой: {card}. Атакующий может подкинуть еще"
            else:
                self.end_round()
                return f"Ты отбился картой: {card}. Раунд окончен!"
        else:
            return "Этой картой нельзя побить"
    
    def player_pass(self) -> str:
        """Игрок пасует (не подкидывает)"""
        if self.current_action != "add":
            return "Сейчас нельзя пасовать"
        
        self.end_round()
        return "Ты пасуешь. Раунд окончен!"
    
    def player_take_cards(self) -> str:
        """Игрок забирает карты"""
        if self.current_action != "defend":
            return "Сейчас нельзя брать карты"
        
        self.players[self.defender].extend(self.table)
        self.table = []
        self.end_round(taken=True)
        return "Ты забрал карты со стола"
    
    def end_round(self, taken: bool = False):
        """Завершение раунда"""
        if not taken:
            # Успешная защита - карты уходят в биту
            self.table = []
        
        # Добор карт
        if self.deck:
            for i in range(2):
                self.draw_cards(i, 6 - len(self.players[i]))
        
        # Смена ролей если защищающийся успешно отбился
        if not taken:
            self.attacker, self.defender = self.defender, self.attacker
        
        self.round_over = True
        self.current_action = "attack"
    
    def bot_make_move(self) -> str:
        """Ход бота"""
        if self.current_action == "attack" and self.attacker == 1:
            # Бот атакует
            for card in self.players[1]:
                if not self.table or self.can_add_card(card):
                    self.players[1].remove(card)
                    self.table.append(card)
                    self.current_action = "defend"
                    return f"🤖 Бот атакует картой: {card}"
            return "🤖 Бот не может атаковать"
            
        elif self.current_action == "defend" and self.defender == 1:
            # Бот защищается
            if len(self.table) % 2 == 1:  # Есть карта для отбивания
                attack_card = self.table[-1]
                for card in self.players[1]:
                    if card.can_beat(attack_card, self.trump.suit):
                        self.players[1].remove(card)
                        self.table.append(card)
                        
                        # Проверяем можно ли подкинуть еще
                        if len(self.players[self.attacker]) > 0 and len(self.table) < 12:
                            self.current_action = "add"
                            return f"🤖 Бот отбивается картой: {card}"
                        else:
                            self.end_round()
                            return f"🤖 Бот отбивается картой: {card}. Раунд окончен!"
                
                # Бот не может побить - забирает карты
                self.players[1].extend(self.table)
                self.table = []
                self.end_round(taken=True)
                return "🤖 Бот забирает карты"
        
        elif self.current_action == "add" and self.attacker == 1:
            # Бот подкидывает карты
            for card in self.players[1]:
                if self.can_add_card(card):
                    self.players[1].remove(card)
                    self.table.append(card)
                    self.current_action = "defend"
                    return f"🤖 Бот подкидывает: {card}"
            
            # Бот пасует
            self.end_round()
            return "🤖 Бот пасует. Раунд окончен!"
        
        return "🤖 Бот пропускает ход"
    
    def check_game_over(self):
        """Проверка окончания игры"""
        # Игра заканчивается когда у кого-то кончились карты и колода пуста
        if not self.players[0] and not self.deck:
            self.game_over = True
            self.winner = "player"
        elif not self.players[1] and not self.deck:
            self.game_over = True
            self.winner = "bot"