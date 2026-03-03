from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from config import ADMIN_ID, RATES, CURRENCY_NAMES
from keyboards.keyboards import (
    get_main_keyboard,
    get_service_action_keyboard,
    get_chat_keyboard,
    get_currency_keyboard,
    get_confirm_keyboard
)
from states.states import ChatStates, ServiceStates, ExchangeStates

router = Router()

# --- START COMMAND ---

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Добро пожаловать в LamKao Exchange!\n\n"
        "Выберите операцию:",
        reply_markup=get_main_keyboard()
    )

# --- ОБРАБОТКА ОПЛАТЫ СЕРВИСА (ФИНАЛ СБОРА ЗАЯВКИ) ---

@router.message(ServiceStates.waiting_for_description)
async def process_service_description(message: Message, state: FSMContext, bot: Bot):
    """Клиент прислал описание/сумму. Заявка готова."""
    description = message.text
    data = await state.get_data()
    photo_id = data.get('service_photo') # Получаем ID фото, которое клиент скинул шагом ранее
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"

    # Формируем красивую карточку для админа
    caption = (
        f"💳 <b>НОВАЯ ЗАЯВКА НА СЕРВИС</b>\n"
        f"👤 Клиент: @{username} (ID: <code>{user_id}</code>)\n"
        f"📝 Запрос: {description}"
    )

    # Клавиатура управления для Админа
    keyboard = get_service_action_keyboard(user_id)

    # Отправляем админу фото + текст + кнопки
    if photo_id:
        await bot.send_photo(ADMIN_ID, photo=photo_id, caption=caption, reply_markup=keyboard, parse_mode="HTML")
    else:
        # Если вдруг фото нет (хотя по логике должно быть), шлем просто текст
        await bot.send_message(ADMIN_ID, caption, reply_markup=keyboard, parse_mode="HTML")

    await message.answer("✅ Заявка отправлена менеджеру! Ожидайте расчета стоимости.")
    await state.clear()

# --- ЧАТ С МЕНЕДЖЕРОМ (КЛИЕНТСКАЯ ЧАСТЬ) ---

@router.message(ChatStates.in_chat)
async def process_chat_message(message: Message, bot: Bot):
    """Клиент пишет сообщение, находясь в режиме чата."""
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"

    # Формируем сообщение для админа
    admin_text = (
        f"📩 <b>Сообщение от клиента</b> @{username}:\n\n"
        f"{message.text}"
    )

    # Прикрепляем ту же клавиатуру действий, чтобы админ мог сразу ответить или выставить счет
    keyboard = get_service_action_keyboard(user_id)

    await bot.send_message(ADMIN_ID, admin_text, reply_markup=keyboard, parse_mode="HTML")
    
    # Подтверждаем клиенту (опционально, можно убрать, чтобы не спамить)
    # await message.answer("Отправлено.", reply_markup=get_chat_keyboard())

@router.callback_query(F.data == "stop_chat")
async def stop_chat_user(callback: CallbackQuery, state: FSMContext):
    """Клиент нажал кнопку выхода из чата."""
    await state.clear()
    await callback.message.answer("Вы вышли из режима чата.", reply_markup=get_main_keyboard())
    await callback.answer()

# --- ОПЛАТА СЧЕТА ---

@router.callback_query(F.data.startswith("service_paid:"))
async def process_service_paid(callback: CallbackQuery, bot: Bot):
    """Клиент нажал 'Я оплатил'."""
    amount = callback.data.split(":")[1]
    username = callback.from_user.username or "NoUsername"
    
    await bot.send_message(
        ADMIN_ID, 
        f"💰 <b>ОПЛАТА СЕРВИСА!</b>\nКлиент @{username} оплатил <b>{amount} RUB</b>.\nПроверьте поступление.",
        parse_mode="HTML"
    )
    await callback.message.edit_text(f"✅ Вы сообщили об оплате {amount} RUB.\nМенеджер проверит и пришлет чек/код.")
    await callback.answer()

# --- ОБМЕН ВАЛЮТЫ ---

@router.callback_query(F.data == "buy_vnd")
async def start_exchange(callback: CallbackQuery, state: FSMContext):
    """Клиент нажал 'Обменять валюту'."""
    await callback.message.answer(
        "🔄 Выберите валюту для обмена:",
        reply_markup=get_currency_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("currency:"))
async def choose_currency(callback: CallbackQuery, state: FSMContext):
    """Клиент выбрал валюту."""
    currency = callback.data.split(":")[1]
    currency_name = CURRENCY_NAMES.get(currency, currency)
    
    await state.update_data(currency=currency)
    await callback.message.answer(
        f"✅ Выбрано: {currency_name}\n\n"
        f"💰 Введите сумму в {currency_name}:"
    )
    await state.set_state(ExchangeStates.entering_amount)
    await callback.answer()


@router.message(ExchangeStates.entering_amount)
async def enter_amount(message: Message, state: FSMContext):
    """Клиент ввел сумму."""
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите число. Нажмите /cancel для отмены.")
        return
    
    amount = int(message.text)
    if amount <= 0:
        await message.answer("Сумма должна быть больше 0. Попробуйте снова.")
        return
    
    data = await state.get_data()
    currency = data.get("currency")
    rate = RATES.get(currency, 0)
    vnd_amount = amount * rate
    currency_name = CURRENCY_NAMES.get(currency, currency)
    
    await state.update_data(
        amount=amount,
        vnd_amount=vnd_amount
    )
    
    await message.answer(
        f"📊 <b>Проверьте данные:</b>\n\n"
        f"💵 Вы отдаёте: <b>{amount} {currency_name}</b>\n"
        f"💴 Получаете: <b>{vnd_amount:,} VND</b>\n\n"
        f"Курс: 1 {currency} = {rate:,} VND",
        reply_markup=get_confirm_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(ExchangeStates.confirming)


@router.callback_query(F.data == "confirm_exchange")
async def confirm_exchange(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Клиент подтвердил обмен."""
    user_id = callback.from_user.id
    username = callback.from_user.username or "Без username"
    
    data = await state.get_data()
    currency = data.get("currency")
    amount = data.get("amount")
    vnd_amount = data.get("vnd_amount")
    currency_name = CURRENCY_NAMES.get(currency, currency)
    
    admin_text = (
        f"🔄 <b>ЗАЯВКА НА ОБМЕН ВАЛЮТЫ</b>\n\n"
        f"👤 Клиент: @{username} (ID: <code>{user_id}</code>)\n"
        f"💵 Отдаёт: <b>{amount} {currency_name}</b>\n"
        f"💴 Получает: <b>{vnd_amount:,} VND</b>"
    )
    
    await bot.send_message(
        ADMIN_ID,
        admin_text,
        parse_mode="HTML"
    )
    
    await callback.message.edit_text(
        f"✅ Заявка отправлена!\n\n"
        f"Менеджер свяжется с вами в ближайшее время.\n"
        f"Курс обмена: 1 {currency} = {RATES.get(currency, 0):,} VND",
        reply_markup=get_main_keyboard()
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню."""
    await state.clear()
    await callback.message.answer(
        "Выберите операцию:",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()