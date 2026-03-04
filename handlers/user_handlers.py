from decimal import Decimal

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from config import ADMIN_ID, RATES, CURRENCY_NAMES
from keyboards.keyboards import (
    get_main_keyboard,
    get_service_action_keyboard,
    get_service_confirm_keyboard,
    get_currency_keyboard,
    get_confirm_keyboard,
    get_exchange_keyboard
)
from states.states import ChatStates, ServiceStates, ExchangeStates
from utils.validators import clean_decimal, decimal_to_int_safe
from database.models import User, Transaction, TransactionStatus

router = Router()

# --- START COMMAND ---

@router.message(Command("start"), StateFilter('*'))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Добро пожаловать в LamKao Exchange!\n\n"
        "Выберите операцию:",
        reply_markup=get_main_keyboard()
    )


@router.message(Command("cancel"), StateFilter('*'))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Действие отменено.",
        reply_markup=get_main_keyboard()
    )


@router.message(Command("rates"))
async def cmd_rates(message: Message):
    # Безопасное форматирование без конфликта кавычек
    rub_formatted = format(RATES['RUB'], ',').replace(',', ' ')
    usdt_formatted = format(RATES['USDT'], ',').replace(',', ' ')
    usd_formatted = format(RATES['USD'], ',').replace(',', ' ')

    await message.answer(
        f"📊 <b>Актуальный курс обмена на сегодня:</b>\n\n"
        f"🇷🇺 1 RUB = {rub_formatted} VND\n"
        f"🪙 1 USDT = {usdt_formatted} VND\n"
        f"💵 1 USD (наличные) = {usd_formatted} VND\n\n"
        f"<i>Курс может незначительно меняться, точный расчет доступен при оформлении заявки.</i>",
        parse_mode="HTML"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "🌴 <b>LamKao Exchange — ваш надежный финансовый сервис во Вьетнаме (Муйне)</b>\n\n"
        "🕒 Время работы: 09:00 - 21:00\n"
        "📍 Выдача наличных: на ресепшене по секретному коду.\n\n"
        "У нас вы можете:\n"
        "- Обменять рубли, доллары и крипту на донги.\n"
        "- Оплатить вьетнамские сервисы (визы, отели, билеты) по QR-коду.\n\n"
        "Если у вас возникли проблемы, нажмите кнопку «Связаться с менеджером» в главном меню.",
        parse_mode="HTML"
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
async def process_chat_message(message: Message, state: FSMContext, bot: Bot):
    """Клиент пишет сообщение, находясь в режиме чата."""
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"

    # Формируем сообщение для админа
    admin_text = (
        f"📩 <b>Сообщение от клиента</b> @{username}:\n\n"
        f"{message.text}"
    )

    # Читаем данные из state клиента
    data = await state.get_data()
    chat_type = data.get("chat_type")
    
    if chat_type == "exchange":
        # Если это обмен - возвращаем кнопку "Одобрить"
        keyboard = get_exchange_keyboard(
            user_id=user_id,
            amount=data.get("exchange_amount", ""),
            currency=data.get("exchange_currency", ""),
            vnd_amount=data.get("exchange_vnd_amount", 0)
        )
    else:
        # Иначе (сервис) - кнопку "Выставить счет"
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
    user_id = callback.from_user.id
    
    await bot.send_message(
        ADMIN_ID, 
        f"💰 <b>ОПЛАТА СЕРВИСА!</b>\nКлиент @{username} оплатил <b>{amount} RUB</b>.\nПроверьте поступление.",
        parse_mode="HTML",
        reply_markup=get_service_confirm_keyboard(user_id)
    )
    await callback.message.edit_text(f"✅ Вы сообщили об оплате {amount} RUB.\nМенеджер проверит и пришлет чек/код.")
    await callback.answer()

# --- ОБМЕН ВАЛЮТЫ ---

@router.callback_query(F.data == "buy_vnd", StateFilter('*'))
async def start_exchange(callback: CallbackQuery, state: FSMContext):
    """Клиент нажал 'Обменять валюту'."""
    await state.clear()
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


@router.message(ExchangeStates.entering_amount, F.text)
async def enter_amount(message: Message, state: FSMContext, session: AsyncSession):
    """Клиент ввел сумму с валидацией."""
    amount_dec = clean_decimal(message.text)
    
    if amount_dec is None or amount_dec <= Decimal('0'):
        await message.answer(
            "Пожалуйста, введите корректную сумму (число больше 0).\n"
            "Нажмите /cancel для отмены."
        )
        return
    
    data = await state.get_data()
    currency = data.get("currency", "")
    rate = RATES.get(currency, 0)
    
    # Используем Decimal для точного расчета
    rate_dec = Decimal(str(rate))
    vnd_amount_dec = amount_dec * rate_dec
    vnd_amount = decimal_to_int_safe(vnd_amount_dec)  # Безопасное преобразование в int
    
    currency_name = CURRENCY_NAMES.get(currency, currency)
    
    user = await session.get(User, message.from_user.id)
    if not user:
        user = User(
            telegram_id=message.from_user.id,
            username=message.from_user.username
        )
        session.add(user)
    
    # Сохраняем в БД (float с округлением до 2 знаков для суммы, целое для VND)
    transaction = Transaction(
        user_id=message.from_user.id,
        amount=float(round(amount_dec, 2)),
        currency=currency,
        vnd_amount=float(vnd_amount),  # Храним как float, но значение целое
        status=TransactionStatus.PENDING
    )
    session.add(transaction)
    await session.flush()
    
    transaction_id = transaction.id
    
    # Сохраняем Decimal и int в state
    await state.update_data(
        amount=amount_dec,
        vnd_amount=vnd_amount,
        transaction_id=transaction_id
    )
    
    # Форматируем отображение
    amount_display = f"{amount_dec:,.2f}".replace(",", " ")
    
    await message.answer(
        f"📊 <b>Проверьте данные:</b>\n\n"
        f"💵 Вы отдаёте: <b>{amount_display} {currency_name}</b>\n"
        f"💴 Получаете: <b>{vnd_amount:,} VND</b>\n\n"
        f"Курс: 1 {currency} = {rate:,} VND",
        reply_markup=get_confirm_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(ExchangeStates.confirming)


@router.callback_query(F.data == "confirm_exchange")
async def confirm_exchange(callback: CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession):
    """ШАГ 1: Клиент подтвердил обмен."""
    user_id = callback.from_user.id
    username = callback.from_user.username or "Без username"
    
    data = await state.get_data()
    currency = data.get("currency", "")
    amount_dec: Decimal | None = data.get("amount")
    vnd_amount: int = data.get("vnd_amount", 0)
    transaction_id = data.get("transaction_id")
    currency_name = CURRENCY_NAMES.get(currency, currency)
    
    if transaction_id:
        transaction = await session.get(Transaction, transaction_id)
        if transaction:
            transaction.status = TransactionStatus.WAITING_FOR_APPROVE
    
    # Форматируем сумму для отображения
    amount_display = f"{amount_dec:,.2f}".replace(",", " ") if amount_dec else "0"
    
    admin_text = (
        f"🔄 <b>ЗАЯВКА НА ОБМЕН ВАЛЮТЫ</b>\n\n"
        f"👤 Клиент: @{username} (ID: <code>{user_id}</code>)\n"
        f"💵 Отдаёт: <b>{amount_display} {currency_name}</b>\n"
        f"💴 Получает: <b>{vnd_amount:,} VND</b>"
    )
    
    await bot.send_message(
        ADMIN_ID,
        admin_text,
        parse_mode="HTML",
        reply_markup=get_exchange_keyboard(user_id, f"{amount_display} {currency}", currency, vnd_amount)
    )
    
    await callback.message.edit_text(
        "✅ Заявка отправлена!\n\n"
        "Менеджер свяжется с вами в ближайшее время.",
        reply_markup=get_main_keyboard()
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "back_to_menu", StateFilter('*'))
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню."""
    await state.clear()
    await callback.message.answer(
        "Выберите операцию:",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("exchange_paid:"))
async def process_exchange_paid(callback: CallbackQuery, bot: Bot):
    """ШАГ 3: Клиент нажал 'Я оплатил'."""
    # Парсим данные из callback_data: "exchange_paid:1000 RUB:RUB:270000"
    parts = callback.data.split(":")
    amount = parts[1]   # "1000 RUB"
    vnd_amount_str = parts[3]
    vnd_amount = decimal_to_int_safe(Decimal(vnd_amount_str))  # Безопасное преобразование
    
    username = callback.from_user.username or "Без username"
    user_id = callback.from_user.id
    
    # Формируем клавиатуру для админа
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Деньги пришли", 
        callback_data=f"exchange_confirmed:{user_id}:{vnd_amount}",
        style="success"
    )
    
    await bot.send_message(
        ADMIN_ID, 
        f"💰 <b>ОПЛАТА ОБМЕНА ВАЛЮТЫ!</b>\n"
        f"Клиент @{username} оплатил <b>{amount}</b>.\n"
        f"Получить: <b>{vnd_amount:,} VND</b>\n\n"
        f"Проверьте поступление и нажмите кнопку ниже.",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    
    await callback.message.edit_text(
        f"✅ Вы сообщили об оплате {amount}.\n"
        f"Менеджер проверит и пришлет код доступа.",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()