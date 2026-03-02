from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
import random

from config import ADMIN_ID, ADMIN_CARD
from keyboards.keyboards import (
    get_admin_order_keyboard,
    get_admin_payment_confirm_keyboard,
    get_payment_confirm_keyboard,
    get_chat_keyboard,
    get_admin_chat_keyboard,
)
from states.states import AdminChat

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


@router.callback_query(F.data.startswith("chat_reply:"))
async def handle_admin_reply_start(callback: CallbackQuery, state: FSMContext, bot: Bot):
    client_id = callback.data.split(":")[1]
    
    await state.update_data(client_to_reply=int(client_id))
    await state.set_state(AdminChat.replying_to_user)
    
    await callback.message.edit_reply_markup(reply_markup=None)
    
    await callback.message.answer(
        f"Введите ваш ответ для клиента (ID: {client_id}):"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("chat_end:"))
async def handle_admin_end_chat(callback: CallbackQuery, bot: Bot):
    client_id = int(callback.data.split(":")[1])
    
    await bot.send_message(
        client_id,
        "Менеджер завершил чат. Если у вас новый вопрос, начните заново."
    )
    
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"Вы завершили чат с клиентом (ID: {client_id}).")
    await callback.answer()


@router.message(AdminChat.replying_to_user)
async def handle_admin_response(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    client_id = data.get("client_to_reply")
    
    if not client_id:
        await message.answer("Ошибка: клиент не найден.")
        await state.clear()
        return
    
    await bot.send_message(
        client_id,
        f"💬 Ответ от менеджера:\n\n{message.text}",
        reply_markup=get_chat_keyboard()
    )
    
    await message.answer(f"✅ Ваш ответ отправлен клиенту (ID: {client_id}).")
    await state.clear()
