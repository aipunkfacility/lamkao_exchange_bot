from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import ADMIN_ID, SBER_CARD
from keyboards.keyboards import (
    ServiceCallback,
    get_service_action_keyboard
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
    """Админ нажал 'Написать/Ответить'."""
    await state.update_data(reply_client_id=callback_data.user_id)
    await state.set_state(AdminChat.replying_to_user)
    await callback.message.answer(f"Введите ответ для клиента (ID: {callback_data.user_id}):")
    await callback.answer()

@router.message(AdminChat.replying_to_user, F.from_user.id == ADMIN_ID)
async def send_admin_reply(message: Message, state: FSMContext, bot: Bot):
    """Админ отправил текст ответа."""
    data = await state.get_data()
    client_id = data.get('reply_client_id')

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
    except Exception as e:
        await message.answer(f"⚠️ Сообщение ушло, но не удалось перевести клиента в режим чата: {e}")

    # 3. Возвращаем админу меню управления
    await message.answer("✅ Ответ отправлен.")
    keyboard = get_service_action_keyboard(client_id)
    await message.answer("Меню управления заявкой:", reply_markup=keyboard)
    
    await state.clear()

@router.callback_query(ServiceCallback.filter(F.action == "reject"))
async def reject_service(callback: CallbackQuery, callback_data: ServiceCallback, bot: Bot):
    """Админ отклонил заявку."""
    try:
        await bot.send_message(callback_data.user_id, "❌ Ваша заявка отклонена менеджером.")
    except:
        pass
    await callback.message.edit_text("❌ Заявка отклонена.")
    await callback.answer()