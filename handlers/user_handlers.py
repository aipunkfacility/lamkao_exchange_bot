from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import RATES, ADMIN_ID, ADMIN_CARD, INPUT_CURRENCY, CURRENCY_NAMES
from keyboards.keyboards import (
    get_main_keyboard,
    get_currency_keyboard,
    get_confirm_keyboard,
    get_admin_order_keyboard,
)
from states.states import ExchangeStates

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
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


@router.callback_query(F.data == "back_to_menu")
async def handle_back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Добро пожаловать в LamKao Exchange!\nВыберите операцию:",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


@router.callback_query(ExchangeStates.select_currency)
async def process_currency_selection(callback: CallbackQuery, state: FSMContext):
    currency_code = callback.data.replace("currency:", "")
    rate = RATES.get(currency_code)
    input_currency = INPUT_CURRENCY.get(currency_code, "рублях")
    
    if rate:
        await state.update_data(currency=currency_code, rate=rate)
        await callback.message.edit_text(
            f"Введите сумму в {input_currency}, которую хотите обменять:"
        )
        await state.set_state(ExchangeStates.enter_amount)
    
    await callback.answer()


@router.message(ExchangeStates.enter_amount)
async def process_amount_input(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        if amount <= 0:
            await message.answer("Сумма должна быть положительной. Попробуйте снова:")
            return
        
        data = await state.get_data()
        rate = data["rate"]
        currency = data["currency"]
        vnd_amount = int(amount * rate)
        
        if currency == "RUB":
            amount_display = f"{int(amount):,} RUB"
        elif currency == "USDT":
            amount_display = f"{amount:.2f} USDT"
        else:
            amount_display = f"{amount:.2f} USD"
        
        await state.update_data(
            amount=amount,
            amount_vnd=vnd_amount,
            amount_display=amount_display
        )
        
        await message.answer(
            f"🔄 Ваша заявка:\n"
            f"Отдаете: {amount_display}\n"
            f"Получаете: {vnd_amount:,} VND\n"
            f"Подтверждаете?",
            reply_markup=get_confirm_keyboard()
        )
        await state.set_state(ExchangeStates.confirm_exchange)
        
    except ValueError:
        await message.answer("Пожалуйста, введите число. Попробуйте снова:")


@router.callback_query(F.data == "back_to_amount")
async def handle_back_to_amount(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    currency = data.get("currency", "RUB")
    input_currency = INPUT_CURRENCY.get(currency, "рублях")
    
    await state.set_state(ExchangeStates.enter_amount)
    await callback.message.edit_text(
        f"Введите сумму в {input_currency}, которую хотите обменять:"
    )
    await callback.answer()


@router.callback_query(ExchangeStates.confirm_exchange)
async def process_confirmation(callback: CallbackQuery, state: FSMContext, bot):
    user_id = callback.from_user.id
    username = callback.from_user.username or "Без username"
    
    if callback.data == "confirm_exchange":
        data = await state.get_data()
        amount_display = data["amount_display"]
        amount_vnd = data["amount_vnd"]
        
        await callback.message.edit_text(
            "Заявка отправлена менеджеру. Ожидайте реквизиты."
        )
        
        await bot.send_message(
            ADMIN_ID,
            f"🔔 НОВАЯ ЗАЯВКА!\n"
            f"Клиент: @{username} (ID: {user_id})\n"
            f"Отдает: {amount_display}\n"
            f"Нужно выдать: {amount_vnd:,} VND",
            reply_markup=get_admin_order_keyboard(user_id, amount_display, amount_vnd, username)
        )
        
    elif callback.data == "cancel_exchange":
        await state.clear()
        await callback.message.edit_text(
            "Заявка отменена.\n/start - начать заново"
        )
    
    await callback.answer()


@router.callback_query(F.data == "user_paid")
async def handle_user_paid(callback: CallbackQuery, state: FSMContext, bot):
    data = await state.get_data()
    amount_display = data.get("amount_display", "N/A")
    
    await bot.send_message(
        ADMIN_ID,
        f"💰 Клиент @{callback.from_user.username} сообщил об оплате {amount_display}."
    )
    
    await callback.message.edit_text("Ожидайте подтверждения от менеджера...")
    await callback.answer()
