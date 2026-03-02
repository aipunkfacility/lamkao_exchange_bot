from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
import random

from config import ADMIN_ID, ADMIN_CARD
from keyboards.keyboards import (
    get_admin_order_keyboard,
    get_admin_payment_confirm_keyboard,
    get_payment_confirm_keyboard,
)

router = Router()

user_sessions = {}


@router.callback_query(F.data.startswith("approve:"))
async def handle_approve(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split(":")
    user_id = int(parts[1])
    amount_display = parts[2].replace("_", " ")
    amount_vnd = int(parts[3])
    username = parts[4]
    
    order_number = random.randint(1000, 9999)
    
    await bot.send_message(
        user_id,
        f"✅ Заявка одобрена!\n"
        f"Переведите {amount_display} на карту Сбербанка: {ADMIN_CARD}\n"
        f"После перевода нажмите кнопку ниже.",
        reply_markup=get_payment_confirm_keyboard()
    )
    
    user_sessions[user_id] = {
        "amount_display": amount_display,
        "amount_vnd": amount_vnd,
        "order_number": order_number
    }
    
    await callback.message.edit_text(
        f"✅ Заявка одобрена для @{username}\n"
        f"Заказ #{order_number} создан"
    )
    
    await bot.send_message(
        ADMIN_ID,
        "Выберите действие:",
        reply_markup=get_admin_payment_confirm_keyboard(user_id)
    )
    
    await callback.answer()


@router.callback_query(F.data.startswith("reject:"))
async def handle_reject(callback: CallbackQuery, bot: Bot):
    user_id = int(callback.data.split(":")[1])
    
    await bot.send_message(
        user_id,
        "❌ К сожалению, ваша заявка отклонена. Попробуйте позже или свяжитесь с менеджером."
    )
    
    await callback.message.edit_text("Заявка отклонена")
    await callback.answer()


@router.callback_query(F.data.startswith("payment_confirmed:"))
async def handle_payment_confirmed(callback: CallbackQuery, bot: Bot):
    user_id = int(callback.data.split(":")[1])
    session = user_sessions.get(user_id)
    
    if session:
        order_number = session["order_number"]
        amount_vnd = session["amount_vnd"]
        
        await bot.send_message(
            user_id,
            f"✅ Оплата получена! Подойдите на ресепшен и назовите код: "
            f"Заказ #{order_number}. Вам выдадут {amount_vnd:,} VND."
        )
        
        await bot.send_message(
            ADMIN_ID,
            f"✅ Заказ #{order_number} сгенерирован и отправлен клиенту "
            f"для выдачи {amount_vnd:,} VND."
        )
        
        await callback.message.edit_text(f"✅ Заказ #{order_number} завершен")
        del user_sessions[user_id]
    
    await callback.answer()
