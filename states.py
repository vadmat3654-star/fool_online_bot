from aiogram.fsm.state import State, StatesGroup

class GameStates(StatesGroup):
    waiting_for_players = State()
    player_turn = State()
    choosing_card = State()
    tournament_registration = State()

class MultiplayerStates(StatesGroup):
    creating_game = State()
    joining_game = State()

class PaymentStates(StatesGroup):
    waiting_payment = State()