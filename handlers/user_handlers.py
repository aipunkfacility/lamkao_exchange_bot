from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from config import ADMIN_ID
from keyboards.keyboards import (
    get_main_keyboard,
    get_service_action_keyboard,
    get_chat_keyboard
)
from states.states import ChatStates, ServiceStates

router = Router()

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
        f"💰 <b>ОПЛАТА СЕРВИСА!</b>\nКлиент @{username} оплатил <b>{amount} RUB</b>.\nПроверьте поступление."
    )
    await callback.message.edit_text(f"✅ Вы сообщили об оплате {amount} RUB.\nМенеджер проверит и пришлет чек/код.")
    await callback.answer()