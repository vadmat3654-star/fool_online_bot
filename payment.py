from aiogram.types import LabeledPrice, PreCheckoutQuery, SuccessfulPayment
from aiogram import Bot
import config

async def create_stars_invoice(bot: Bot, user_id: int, amount: int):
    """Создание инвойса для покупки звёзд"""
    
    prices = [LabeledPrice(label=f"{amount} звёзд", amount=amount * 100)]  # в копейках
    
    await bot.send_invoice(
        chat_id=user_id,
        title="Покупка звёзд",
        description=f"Пополнение баланса на {amount} звёзд",
        payload=f"stars_{amount}",
        provider_token="YOUR_PROVIDER_TOKEN",  # Нужно получить у @id199142634 (@BotFather)
        currency="XTR",  # Telegram Stars
        prices=prices,
        start_parameter="stars-purchase",
        need_email=False,
        need_phone_number=False,
        need_shipping_address=False,
        is_flexible=False
    )
    
async def process_stars_payment(user_id: int, amount: int):
    """Заглушка для платежей (пока не подключена ЮKassa)"""
    from database import SessionLocal, Player
    
    with SessionLocal() as session:
        player = session.get(Player, user_id)
        player.stars += amount
        session.commit()
    
    return True