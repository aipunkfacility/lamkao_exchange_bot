import random
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import ADMIN_ID, SBER_CARD
from keyboards.keyboards import (
    ServiceCallback,
    ExchangeCallback,
    get_service_action_keyboard,
    get_exchange_keyboard,
    get_main_keyboard
)
from states.states import AdminChat, AdminStates, ChatStates

router = Router()

# --- ОБРАБОТКА ЗАЯВКИ НА СЕРВИС (ВЫСТАВИТЬ СЧЕТ) ---

@router.callback_query(ServiceCallback.filter(F.action == "bill"))
async def start_service_bill(callback: CallbackQuery, callback_data: ServiceCallback, state: FSMContext):
    """Админ нажал 'Выставить счет'."""
    await state.update_data(bill_client_id=callback_data.user_id)
    await state.set_state(AdminStates.waiting_for_service_amount)
    await callback.message.answer("Введите сумму счета в РУБЛЯХ (только число):")
    await callback.answer()

@router.message(AdminStates.waiting_for_service_amount, F.from_user.id == ADMIN_ID)
async def process_service_bill_amount(message: Message, state: FSMContext, bot: Bot):
    """Админ ввел сумму счета."""
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите только число.")
        return

    amount = int(message.text)
    data = await state.get_data()
    client_id = data.get('bill_client_id')

    # Формируем кнопку оплаты для клиента
    builder = InlineKeyboardBuilder()
    builder.button(text="🧾 Я оплатил", callback_data=f"service_paid:{amount}")
    
    # Отправляем счет клиенту
    try:
        await bot.send_message(
            client_id,
            f"✅ <b>Заявка подтверждена!</b>\n\n"
            f"К оплате: <b>{amount} RUB</b>\n"
            f"Реквизиты: <code>{SBER_CARD}</code>\n\n"
            f"После перевода нажмите кнопку ниже.",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
    except Exception as e:
        await message.answer(f"Ошибка отправки клиенту: {e}")
        await state.clear()
        return

    # Возвращаем админу управление
    await message.answer(f"✅ Счет на {amount} RUB выставлен клиенту.")
    
    # Показываем меню действий, чтобы админ мог продолжить общение
    keyboard = get_service_action_keyboard(client_id)
    await message.answer("Меню управления заявкой:", reply_markup=keyboard)
    await state.clear()

# --- ЛОГИКА ЧАТА (ОТВЕТ АДМИНА) ---

@router.callback_query(ServiceCallback.filter(F.action == "reply"))
async def start_admin_reply(callback: CallbackQuery, callback_data: ServiceCallback, state: FSMContext):
    """Админ нажал 'Написать/Ответить' для сервиса."""
    await state.update_data(
        reply_client_id=callback_data.user_id,
        chat_type="service"
    )
    await state.set_state(AdminChat.replying_to_user)
    await callback.message.answer(f"Введите ответ для клиента (ID: {callback_data.user_id}):")
    await callback.answer()

@router.message(AdminChat.replying_to_user, F.from_user.id == ADMIN_ID)
async def send_admin_reply(message: Message, state: FSMContext, bot: Bot):
    """Админ отправил текст ответа."""
    data = await state.get_data()
    client_id = data.get('reply_client_id')
    chat_type = data.get('chat_type', 'service')

    # 1. Отправляем сообщение клиенту
    try:
        # Кнопка для клиента, чтобы выйти из чата (опционально)
        client_kb = InlineKeyboardBuilder()
        client_kb.button(text="❌ Завершить чат", callback_data="stop_chat")
        
        await bot.send_message(
            client_id, 
            f"💬 <b>Сообщение от менеджера:</b>\n\n{message.text}",
            parse_mode="HTML",
            reply_markup=client_kb.as_markup()
        )
    except Exception as e:
        await message.answer(f"Не удалось отправить сообщение: {e}")
        await state.clear()
        return

    # 2. ПРИНУДИТЕЛЬНО ПЕРЕВОДИМ КЛИЕНТА В РЕЖИМ ЧАТА (ВАРИАНТ А)
    # Используем StorageKey для доступа к состоянию другого юзера
    try:
        state_key = StorageKey(bot_id=bot.id, chat_id=client_id, user_id=client_id)
        # Создаем контекст. Важно: используем storage из текущего state админа
        client_state = FSMContext(storage=state.storage, key=state_key)
        await client_state.set_state(ChatStates.in_chat)
        
        # ПЕРЕДАЕМ КОНТЕКСТ КЛИЕНТУ:
        admin_data = await state.get_data()
        await client_state.update_data(
            chat_type=admin_data.get("chat_type"),
            exchange_amount=admin_data.get("exchange_amount"),
            exchange_currency=admin_data.get("exchange_currency"),
            exchange_vnd_amount=admin_data.get("exchange_vnd_amount")
        )
    except Exception as e:
        await message.answer(f"⚠️ Сообщение ушло, но не удалось перевести клиента в режим чата: {e}")

    # 3. Возвращаем админу меню управления (в зависимости от типа чата)
    await message.answer("✅ Ответ отправлен.")
    
    if chat_type == "exchange":
        # Для обмена валют - возвращаем клавиатуру обмена
        exchange_amount = data.get('exchange_amount', '')
        exchange_currency = data.get('exchange_currency', '')
        exchange_vnd_amount = data.get('exchange_vnd_amount', 0)
        keyboard = get_exchange_keyboard(client_id, exchange_amount, exchange_currency, exchange_vnd_amount)
    else:
        # Для сервисов - возвращаем клавиатуру сервиса
        keyboard = get_service_action_keyboard(client_id)
    
    await message.answer("Меню управления заявкой:", reply_markup=keyboard)
    
    await state.clear()

@router.callback_query(ServiceCallback.filter(F.action == "reject"))
async def reject_service(callback: CallbackQuery, callback_data: ServiceCallback, bot: Bot):
    """Админ отклонил заявку."""
    try:
        await bot.send_message(callback_data.user_id, "❌ Ваша заявка отклонена менеджером.")
    except Exception:
        pass
    await callback.message.edit_text("❌ Заявка отклонена.")
    await callback.answer()


@router.callback_query(ServiceCallback.filter(F.action == "confirm_pay"))
async def confirm_service_payment(callback: CallbackQuery, callback_data: ServiceCallback, state: FSMContext, bot: Bot):
    """Админ подтвердил оплату. Запрашиваем чек/билет."""
    client_id = callback_data.user_id
    
    # 1. Уведомляем клиента, что процесс пошел
    try:
        await bot.send_message(
            client_id,
            "✅ <b>Оплата получена!</b>\n"
            "Менеджер оформляет ваш заказ. Ожидайте чек/билет/код в следующем сообщении...",
            parse_mode="HTML"
        )
    except Exception:
        pass

    # 2. Переводим админа в режим ожидания файла
    await state.update_data(result_client_id=client_id)
    await state.set_state(AdminStates.waiting_for_service_result)
    
    await callback.message.edit_text(
        "✅ Оплата подтверждена.\n\n"
        "📎 <b>Теперь отправьте итоговый результат для клиента:</b>\n"
        "Это может быть файл (PDF билет), фотография (чек) или просто текст (код бронирования).",
        reply_markup=None,
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_service_result, F.from_user.id == ADMIN_ID)
async def send_service_result_to_client(message: Message, state: FSMContext, bot: Bot):
    """Админ отправил итоговый файл/текст. Пересылаем клиенту."""
    data = await state.get_data()
    client_id = data.get("result_client_id")
    
    if not client_id:
        await message.answer("Ошибка: ID клиента потерян.")
        await state.clear()
        return

    try:
        # Пересылаем 1в1 (фото, PDF, текст)
        await message.copy_to(
            chat_id=client_id,
            caption=message.caption if message.caption else "✅ Ваш заказ выполнен. Спасибо, что выбрали нас!"
        )
        
        # Если это был просто текст, copy_to отправит его
        if not message.photo and not message.document:
            await bot.send_message(client_id, "✅ Ваш заказ выполнен. Спасибо, что выбрали нас!")
        
        await message.answer("✅ Результат успешно отправлен клиенту. Сделка закрыта.")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка при отправке клиенту: {e}")
    
    await state.clear()

# --- ОБРАБОТКА ЗАЯВКИ НА ОБМЕН ВАЛЮТЫ ---

@router.callback_query(ExchangeCallback.filter(F.action == "approve"))
async def approve_exchange(callback: CallbackQuery, callback_data: ExchangeCallback, bot: Bot):
    """ШАГ 2: Админ одобрил заявку на обмен валюты."""
    client_id = callback_data.user_id
    amount = callback_data.amount      # "1000 RUB"
    currency = callback_data.currency  # "RUB"
    vnd_amount = callback_data.vnd_amount  # 270000
    
    # Отправляем реквизиты клиенту с vnd_amount
    builder = InlineKeyboardBuilder()
    builder.button(text="🧾 Я оплатил", callback_data=f"exchange_paid:{amount}:{currency}:{vnd_amount}", style="success")
    
    try:
        await bot.send_message(
            client_id,
            f"✅ <b>Ваша заявка одобрена!</b>\n\n"
            f"Вы отдаёте: <b>{amount}</b>\n"
            f"Получаете: <b>{vnd_amount:,} VND</b>\n\n"
            f"Реквизиты для оплаты:\n"
            f"💳 Сбер: <code>{SBER_CARD}</code>\n\n"
            f"После оплаты нажмите кнопку ниже.",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
        
        await callback.message.edit_text("✅ Заявка одобрено. Реквизиты отправлены клиенту.")
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Не удалось отправить клиенту реквизиты: {e}")
    
    await callback.answer()


@router.callback_query(ExchangeCallback.filter(F.action == "reject"))
async def reject_exchange(callback: CallbackQuery, callback_data: ExchangeCallback, bot: Bot):
    """Админ отклонил заявку на обмен валюты."""
    client_id = callback_data.user_id
    
    try:
        await bot.send_message(client_id, "❌ Менеджер отклонил вашу заявку на обмен.")
    except Exception:
        pass
    
    await callback.message.edit_text("❌ Заявка на обмен валюты отклонена.")
    await callback.answer()


@router.callback_query(ExchangeCallback.filter(F.action == "chat"))
async def start_exchange_chat(callback: CallbackQuery, callback_data: ExchangeCallback, state: FSMContext):
    """Админ нажал 'Уточнить детали' для обмена валюты - просит текст."""
    await state.update_data(
        reply_client_id=callback_data.user_id,
        chat_type="exchange",
        exchange_amount=callback_data.amount,
        exchange_currency=callback_data.currency,
        exchange_vnd_amount=callback_data.vnd_amount
    )
    await state.set_state(AdminChat.replying_to_user)
    await callback.message.answer(f"Введите сообщение для клиента (ID: {callback_data.user_id}):")
    await callback.answer()


@router.callback_query(F.data.startswith("exchange_confirmed:"))
async def confirm_exchange_payment(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Админ подтвердил поступление денег - генерирует PIN."""
    data = callback.data.split(":")
    client_id = int(data[1])
    vnd_amount = int(data[2])
    
    # Генерируем 4-значный PIN
    pin = f"#{random.randint(1000, 9999)}"
    
    # Отправляем PIN клиенту
    try:
        await bot.send_message(
            client_id,
            f"🔑 <b>Ваш секретный код для получения:</b> <b>{pin}</b>\n\n"
            f"Покажите его на ресепшене для получения <b>{vnd_amount:,} VND</b>.\n\n"
            f"✅ Обмен завершен! Спасибо за использование нашего сервиса.",
            parse_mode="HTML"
        )
    except Exception as e:
        await callback.message.edit_text(f"❌ Не удалось отправить PIN клиенту: {e}")
        await callback.answer()
        return
    
    # Очищаем состояние клиента
    try:
        state_key = StorageKey(bot_id=bot.id, chat_id=client_id, user_id=client_id)
        client_state = FSMContext(storage=state.storage, key=state_key)
        await client_state.clear()
    except Exception:
        pass
    
    # Уведомляем админа
    await callback.message.edit_text(
        f"✅ Код {pin} выдан клиенту для получения {vnd_amount:,} VND.",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()