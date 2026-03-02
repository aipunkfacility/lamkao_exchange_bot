from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import RATES, ADMIN_ID, ADMIN_CARD
from keyboards.keyboards import (
    get_main_keyboard,
    get_currency_keyboard,
    get_confirm_keyboard,
    get_payment_confirm_keyboard,
)
from states.states import ExchangeStates

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Добро пожаловать в LamKao Exchange!\nВыберите операцию:",
        reply_markup=get_main_keyboard()
    )


@router.callback_query(F.data == "buy_vnd")
async def handle_buy_vnd(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите валюту, которую хотите отдать:",
        reply_markup=get_currency_keyboard()
    )
    await state.set_state(ExchangeStates.select_currency)
    await callback.answer()


@router.callback_query(F.data == "qr_payment")
async def handle_qr_payment(callback: CallbackQuery):
    await callback.answer("В разработке", show_alert=True)


@router.callback_query(ExchangeStates.select_currency)
async def process_currency_selection(callback: CallbackQuery, state: FSMContext):
    currency_code = callback.data.replace("currency:", "")
    rate = RATES.get(currency_code)
    
    if rate:
        await state.update_data(currency=currency_code, rate=rate)
        await callback.message.edit_text(
            "Введите сумму в рублях, которую хотите обменять:"
        )
        await state.set_state(ExchangeStates.enter_amount)
    
    await callback.answer()


@router.message(ExchangeStates.enter_amount)
async def process_amount_input(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
        if amount <= 0:
            await message.answer("Сумма должна быть положительной. Попробуйте снова:")
            return
        
        data = await state.get_data()
        rate = data["rate"]
        vnd_amount = amount * rate
        
        await state.update_data(amount_rub=amount, amount_vnd=vnd_amount)
        
        await message.answer(
            f"🔄 Ваша заявка:\n"
            f"Отдаете: {amount:,} RUB\n"
            f"Получаете: {vnd_amount:,} VND\n"
            f"Подтверждаете?",
            reply_markup=get_confirm_keyboard()
        )
        await state.set_state(ExchangeStates.confirm_exchange)
        
    except ValueError:
        await message.answer("Пожалуйста, введите число. Попробуйте снова:")


@router.callback_query(ExchangeStates.confirm_exchange)
async def process_confirmation(callback: CallbackQuery, state: FSMContext, bot):
    user_id = callback.from_user.id
    username = callback.from_user.username or "Без username"
    
    if callback.data == "confirm_exchange":
        data = await state.get_data()
        amount_rub = data["amount_rub"]
        amount_vnd = data["amount_vnd"]
        
        await callback.message.edit_text(
            "Заявка отправлена менеджеру. Ожидайте реквизиты."
        )
        
        await bot.send_message(
            ADMIN_ID,
            f"🔔 НОВАЯ ЗАЯВКА!\n"
            f"Клиент: @{username} (ID: {user_id})\n"
            f"Отдает: {amount_rub:,} RUB\n"
            f"Нужно выдать: {amount_vnd:,} VND"
        )
        
    elif callback.data == "cancel_exchange":
        await callback.message.edit_text(
            "Заявка отменена.\n/start - начать заново"
        )
        await state.clear()
    
    await callback.answer()


@router.callback_query(F.data == "user_paid")
async def handle_user_paid(callback: CallbackQuery, state: FSMContext, bot):
    data = await state.get_data()
    amount_rub = data.get("amount_rub", 0)
    
    await bot.send_message(
        ADMIN_ID,
        f"💰 Клиент @{callback.from_user.username} сообщил об оплате {amount_rub:,} RUB."
    )
    
    await callback.message.edit_text("Ожидайте подтверждения от менеджера...")
    await callback.answer()
