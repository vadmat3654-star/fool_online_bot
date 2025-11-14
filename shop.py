from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import db
from keyboards.builders import MenuKeyboards

shop_router = Router()
keyboards = MenuKeyboards()

@shop_router.message(F.text == "🛍️ Магазин")
async def shop_main(message: Message):
    user_stars = db.get_user_stars(message.from_user.id)
    
    await message.answer(
        f"🛍️ Магазин скинов\n\n"
        f"💰 Твой баланс: {user_stars} звезд\n\n"
        f"Выбери категорию:",
        reply_markup=keyboards.shop_categories()
    )

@shop_router.callback_query(F.data == "shop_skins")
async def shop_skins(callback: CallbackQuery):
    skins = db.get_shop_items('skin')
    user_stars = db.get_user_stars(callback.from_user.id)
    
    text = f"🎨 Скины для карт\n\n💰 Баланс: {user_stars} звезд\n\n"
    
    for skin in skins:
        skin_id, name, _, price, rarity, effect, image = skin
        text += f"{image} {name}\n"
        text += f"   Цена: {price} звезд\n"
        text += f"   Редкость: {rarity}\n"
        text += f"   Эффект: {effect}\n\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboards.shop_skins_list(skins)
    )

@shop_router.callback_query(F.data == "shop_boxes")
async def shop_boxes(callback: CallbackQuery):
    boxes = db.get_shop_items('box')
    user_stars = db.get_user_stars(callback.from_user.id)
    
    text = f"🎁 Боксы со скинами\n\n💰 Баланс: {user_stars} звезд\n\n"
    
    for box in boxes:
        box_id, name, _, price, rarity, effect, image = box
        text += f"{image} {name}\n"
        text += f"   Цена: {price} звезд\n"
        text += f"   Редкость: {rarity}\n"
        text += f"   Содержимое: {effect}\n\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboards.shop_boxes_list(boxes)
    )

@shop_router.callback_query(F.data.startswith("buy_"))
async def buy_item(callback: CallbackQuery):
    item_id = int(callback.data.replace("buy_", ""))
    user_id = callback.from_user.id
    
    success, message = db.purchase_item(user_id, item_id)
    
    if success:
        user_stars = db.get_user_stars(user_id)
        await callback.message.edit_text(
            f"✅ {message}\n\n"
            f"💰 Теперь у тебя: {user_stars} звезд\n\n"
            f"Что-то еще?",
            reply_markup=keyboards.shop_after_purchase()
        )
    else:
        await callback.answer(f"❌ {message}", show_alert=True)

@shop_router.callback_query(F.data == "back_to_shop")
async def back_to_shop(callback: CallbackQuery):
    user_stars = db.get_user_stars(callback.from_user.id)
    
    await callback.message.edit_text(
        f"🛍️ Магазин скинов\n\n"
        f"💰 Твой баланс: {user_stars} звезд\n\n"
        f"Выбери категорию:",
        reply_markup=keyboards.shop_categories()
    )

@shop_router.callback_query(F.data == "my_inventory")
async def show_inventory(callback: CallbackQuery):
    """Показать инвентарь"""
    user_id = callback.from_user.id
    
    skins, inventory = db.get_user_inventory(user_id)
    
    text = "📦 Твой инвентарь\n\n"
    
    # Показываем скины
    text += "🎨 Твои скины:\n"
    if skins:
        for skin in skins:
            text += f"• {skin}\n"
    else:
        text += "😔 Пока нет скинов\n"
    
    # Показываем боксы
    text += "\n🎁 Твои боксы:\n"
    boxes = [item for item in inventory if item[0] == "box"]
    if boxes:
        for box_type, box_name, quantity in boxes:
            text += f"• {box_name} - {quantity} шт.\n"
    else:
        text += "😔 Пока нет боксов\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboards.inventory_actions(skins, boxes)
    )

@shop_router.callback_query(F.data.startswith("open_box_"))
async def open_box(callback: CallbackQuery):
    """Открыть бокс"""
    box_name = callback.data.replace("open_box_", "")
    user_id = callback.from_user.id
    
    success, message = db.open_box(user_id, box_name)
    
    if success:
        await callback.message.edit_text(
            f"🎁 Открытие бокса {box_name}!\n\n{message}",
            reply_markup=keyboards.after_box_open()
        )
    else:
        await callback.answer(f"❌ {message}", show_alert=True)

@shop_router.callback_query(F.data.startswith("equip_skin_"))
async def equip_skin(callback: CallbackQuery):
    """Надеть скин"""
    skin_name = callback.data.replace("equip_skin_", "")
    user_id = callback.from_user.id
    
    success, message = db.equip_skin(user_id, skin_name)
    
    if success:
        await callback.message.edit_text(
            f"✅ {message}",
            reply_markup=keyboards.back_to_inventory()
        )
    else:
        await callback.answer(f"❌ {message}", show_alert=True)

@shop_router.callback_query(F.data == "back_to_inventory")
async def back_to_inventory(callback: CallbackQuery):
    """Вернуться в инвентарь"""
    await show_inventory(callback)