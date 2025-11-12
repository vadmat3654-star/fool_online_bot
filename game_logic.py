import random
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class Card:
    suit: str
    rank: str
    
    def __str__(self):
        return f"{self.rank}{self.suit}"
    
    @property
    def value(self):
        values = {'6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 
                 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        return values[self.rank]

class GameEngine:
    SUITS = ['♠', '♥', '♦', '♣']
    RANKS = ['6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    
    def __init__(self):
        self.deck = []
        self.trump = None
        
    def create_deck(self) -> List[Card]:
        """Создание колоды"""
        return [Card(suit, rank) for suit in self.SUITS for rank in self.RANKS]
    
    def shuffle_deck(self, deck: List[Card]) -> List[Card]:
        """Перемешивание колоды"""
        random.shuffle(deck)
        return deck
    
    def deal_cards(self, deck: List[Card], num_players: int) -> List[List[Card]]:
        """Раздача карт"""
        hands = [[] for _ in range(num_players)]
        for i in range(6 * num_players):
            if deck:
                hands[i % num_players].append(deck.pop())
        return hands
    
    def setup_game(self, num_players: int) -> Tuple[List[Card], List[List[Card]], str]:
        """Настройка новой игры"""
        deck = self.create_deck()
        deck = self.shuffle_deck(deck)
        self.trump = deck[0].suit if deck else random.choice(self.SUITS)
        hands = self.deal_cards(deck, num_players)
        
        return deck, hands, self.trump
    
    def can_attack(self, card: Card, table: Dict) -> bool:
        """Можно ли атаковать этой картой"""
        if not table["attacks"]:
            return True
        
        # Можно атаковать картой того же достоинства, что уже на столе
        table_ranks = {c.rank for c in table["attacks"] + [c for c in table["defends"] if c]}
        return card.rank in table_ranks
    
    def can_defend(self, attack_card: Card, defend_card: Card, trump: str) -> bool:
        """Можно ли защититься от атаки"""
        if attack_card.suit == defend_card.suit:
            return defend_card.value > attack_card.value
        elif defend_card.suit == trump:
            return True
        return False
    
    def bot_move_easy(self, hand: List[Card], table: Dict, trump: str) -> Card:
        """Лёгкий бот - случайные ходы"""
        valid_attacks = [card for card in hand if self.can_attack(card, table)]
        return random.choice(valid_attacks) if valid_attacks else None
    
    def bot_move_medium(self, hand: List[Card], table: Dict, trump: str) -> Card:
        """Средний бот - стратегические ходы"""
        valid_attacks = [card for card in hand if self.can_attack(card, table)]
        if not valid_attacks:
            return None
        
        # Предпочитаем некозырные карты
        non_trump = [card for card in valid_attacks if card.suit != trump]
        if non_trump:
            return min(non_trump, key=lambda x: x.value)  # Сначала сбрасываем младшие
        return min(valid_attacks, key=lambda x: x.value)
    
    def bot_move_hard(self, hand: List[Card], table: Dict, trump: str) -> Card:
        """Сложный бот - продвинутая стратегия"""
        valid_attacks = [card for card in hand if self.can_attack(card, table)]
        if not valid_attacks:
            return None
        
        # Сложная логика: учитываем вероятность отбития
        attacks_by_risk = sorted(valid_attacks, key=lambda x: (
            x.suit == trump,  # Козырные в конце
            -x.value  # Старшие карты в начале
        ))
        
        return attacks_by_risk[0]

    def check_win(self, hands: List[List[Card]], deck: List[Card]) -> int:
        """Проверка победы (-1 если нет победителя)"""
        for i, hand in enumerate(hands):
            if not hand and not deck:  # Нет карт на руках и в колоде
                return i
        return -1