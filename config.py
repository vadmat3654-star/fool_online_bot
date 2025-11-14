import os
from dataclasses import dataclass

@dataclass
class Config:
    BOT_TOKEN: str = "8525915886:AAEMqKR9PVNWbRm9jqOhuLGDyBWrHqwXtfQ"
    ADMIN_IDS: list = None
    
    def __post_init__(self):
        if self.ADMIN_IDS is None:
            self.ADMIN_IDS = [123456789]  # Твой ID

config = Config()