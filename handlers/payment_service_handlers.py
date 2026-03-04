from aiogram import Router, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.exceptions import TelegramAPIError

from config import ADMIN_ID
from keyboards.keyboards import (
    get_main_keyboard,
    get_service_request_keyboard,
    get_service_action_keyboard,
    get_service_confirm_keyboard,
    get_exchange_keyboard
)
from states.states import ServiceStates, ChatStates
from database.models import Transaction, TransactionStatus

router = Router()

# --- КОМАНДА ОТМЕНЫ (С ОБНОВЛЕНИЕМ БД) ---
@router.message(Command("cancel"), StateFilter('*'))
async def cmd_cancel_service(message: Message, state: FSMContext, session: AsyncSession = None):
    try:
        if session:
            data = await state.get_data()
            transaction_id = data.get("transaction_id")
            if transaction_id:
                transaction = await session.get(Transaction, transaction_id)
                if transaction and transaction.status == TransactionStatus.PENDING:
                    transaction.status = TransactionStatus.CANCELED
                    await session.commit()
    except Exception:
        pass
    
    await state.clear()
    await message.answer(
        "Действие отменено.",
        reply_markup=get_main_keyboard()
    )

# --- СОЗДАНИЕ ЗАЯВКИ НА СЕРВИС ---
@router.callback_query(F.data == "ask_manager", StateFilter('*'))
async def process_ask_manager(callback: CallbackQuery, state: FSMContext, bot: Bot):
    user_id = callback.from_user.id
    username = callback.from_user.username or "Без username"
    
    await state.clear()
    await state.set_state(ChatStates.in_chat)
    await state.update_data(chat_type="service")
    
    try:
        await bot.send_message(
            ADMIN_ID,
            f"📩 <b>Клиент хочет связаться с менеджером:</b> @{username}\n\n"
            f"Вы можете начать диалог или выставить счет.",
            parse_mode="HTML",
            reply_markup=get_service_request_keyboard(user_id)
        )
    except TelegramAPIError:
        pass
        
    await callback.message.answer(
        "💬 Вы начали диалог с менеджером.\n"
        "Напишите ваш вопрос, и мы ответим в ближайшее время.",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "qr_payment", StateFilter('*'))
async def start_qr_payment(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("📸 Отправьте фото QR-кода или скриншот оплаты:")
    await state.set_state(ServiceStates.waiting_for_photo)
    await callback.answer()

@router.message(ServiceStates.waiting_for_photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=file_id, photo_type="photo")
    
    await message.answer("📝 Теперь введите сумму и описание (например: '1000 RUB, оплата за тур'):")
    await state.set_state(ServiceStates.waiting_for_description)

@router.message(ServiceStates.waiting_for_photo, F.document)
async def process_document(message: Message, state: FSMContext):
    doc = message.document
    if doc.mime_type and doc.mime_type.startswith("image/"):
        await state.update_data(photo_file_id=doc.file_id, photo_type="document")
        await message.answer("📝 Теперь введите сумму и описание (например: '1000 RUB, оплата за тур'):")
        await state.set_state(ServiceStates.waiting_for_description)
    else:
        await message.answer(
            "📷 Пожалуйста, отправьте изображение (фото, скриншот).\n"
            "PDF и другие документы не принимаются.\n"
            "Нажмите /cancel для отмены."
        )

@router.message(ServiceStates.waiting_for_photo)
async def process_invalid_photo(message: Message, state: FSMContext):
    await message.answer(
        "📷 Пожалуйста, отправьте фото QR-кода или скриншота оплаты.\n"
        "Нажмите /cancel для отмены."
    )

@router.message(ServiceStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    username = message.from_user.username or "Без username"
    
    data = await state.get_data()
    photo_file_id = data.get("photo_file_id")
    photo_type = data.get("photo_type", "photo")
    description = message.text
    
    await state.update_data(description=description, username=username)
    
    caption = (
        f"💳 <b>НОВАЯ ЗАЯВКА НА ОПЛАТУ СЕРВИСА</b>\n"
        f"👤 Клиент: @{username} (ID: <code>{user_id}</code>)\n"
        f"📝 Запрос: {description}"
    )
    
    # ПРАВИЛЬНАЯ клавиатура управления для админа
    keyboard = get_service_action_keyboard(user_id)
    
    try:
        if photo_type == "document":
            await bot.send_document(ADMIN_ID, photo_file_id, caption=caption, reply_markup=keyboard, parse_mode="HTML")
        else:
            await bot.send_photo(ADMIN_ID, photo_file_id, caption=caption, reply_markup=keyboard, parse_mode="HTML")
        
        await message.answer("✅ Заявка отправлена менеджерам. Ожидайте подтверждения!", reply_markup=get_main_keyboard())
    except TelegramAPIError:
        await message.answer("❌ Ошибка при отправке заявки. Попробуйте снова или нажмите /cancel.", reply_markup=get_main_keyboard())
    
    await state.clear()

# --- ЧАТ С МЕНЕДЖЕРОМ И ОПЛАТА СЕРВИСА (Перенесено из user_handlers) ---
@router.message(ChatStates.in_chat)
async def process_chat_message(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"

    admin_text = f"📩 <b>Сообщение от клиента</b> @{username}:\n\n{message.text}"
    data = await state.get_data()
    chat_type = data.get("chat_type")
    
    if chat_type == "exchange":
        keyboard = get_exchange_keyboard(
            user_id=user_id,
            amount=data.get("exchange_amount", ""),
            currency=data.get("exchange_currency", ""),
            vnd_amount=data.get("exchange_vnd_amount", 0)
        )
    else:
        keyboard = get_service_action_keyboard(user_id)

    try:
        await bot.send_message(ADMIN_ID, admin_text, reply_markup=keyboard, parse_mode="HTML")
    except TelegramAPIError:
        pass # Ошибка отправки админу

@router.callback_query(F.data == "stop_chat")
async def stop_chat_user(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.answer("Вы вышли из режима чата.", reply_markup=get_main_keyboard())
    except TelegramAPIError:
        pass
    await callback.answer()

@router.callback_query(F.data.startswith("service_paid:"))
async def process_service_paid(callback: CallbackQuery, bot: Bot):
    amount = callback.data.split(":")[1]
    username = callback.from_user.username or "NoUsername"
    user_id = callback.from_user.id
    
    try:
        await bot.send_message(
            ADMIN_ID, 
            f"💰 <b>ОПЛАТА СЕРВИСА!</b>\nКлиент @{username} оплатил <b>{amount} RUB</b>.\nПроверьте поступление.",
            parse_mode="HTML",
            reply_markup=get_service_confirm_keyboard(user_id) # Правильная клавиатура подтверждения
        )
        await callback.message.edit_text(f"✅ Вы сообщили об оплате {amount} RUB.\nМенеджер проверит и пришлет чек/код.")
    except TelegramAPIError:
        await callback.message.answer(f"✅ Вы сообщили об оплате {amount} RUB.\nМенеджер проверит и пришлет чек/код.")
    finally:
        await callback.answer()