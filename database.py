from sqlalchemy import create_engine, Column, BigInteger, String, Integer, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Простая база без заморочек
DATABASE_URL = "sqlite:///fool_game.db"

Base = declarative_base()

class Player(Base):
    __tablename__ = "players"
    user_id = Column(BigInteger, primary_key=True)
    username = Column(String)
    stars = Column(Integer, default=100)
    selected_skin = Column(String, default="default")
    skins = Column(JSON, default=lambda: ["default"])
    daily_reward = Column(DateTime)
    games_played = Column(Integer, default=0)
    games_won = Column(Integer, default=0)
    tournaments_won = Column(Integer, default=0)
    registration_date = Column(DateTime, default=datetime.now)

class ActiveGame(Base):
    __tablename__ = "active_games"
    game_id = Column(String, primary_key=True)
    players = Column(JSON)
    player_order = Column(JSON)
    current_player = Column(BigInteger)
    deck = Column(JSON)
    table = Column(JSON)
    trump = Column(String)
    game_type = Column(String)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.now)

class Tournament(Base):
    __tablename__ = "tournaments"
    tournament_id = Column(String, primary_key=True)
    players = Column(JSON, default=list)
    status = Column(String, default="registration")
    prize_pool = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

# Инициализация
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)