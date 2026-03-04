from aiogram import Router, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID
from keyboards.keyboards import get_main_keyboard, get_service_request_keyboard
from states.states import ServiceStates, ChatStates

router = Router()


# --- /cancel ДОЛЖЕН БЫТЬ ПЕРЕД FSM-хэндлерами ---
@router.message(Command("cancel"), StateFilter('*'))
async def cmd_cancel_service(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Действие отменено.",
        reply_markup=get_main_keyboard()
    )


@router.callback_query(F.data == "ask_manager", StateFilter('*'))
async def process_ask_manager(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Клиент нажал 'Связаться с менеджером' - сбрасываем стейт и создаем чат."""
    user_id = callback.from_user.id
    username = callback.from_user.username or "Без username"
    
    await state.clear()
    await state.set_state(ChatStates.in_chat)
    await state.update_data(chat_type="service")
    
    await bot.send_message(
        ADMIN_ID,
        f"📩 <b>Клиент хочет связаться с менеджером:</b> @{username}\n\n"
        f"Вы можете начать диалог или выставить счет.",
        parse_mode="HTML",
        reply_markup=get_service_request_keyboard(user_id)
    )
    
    await callback.message.answer(
        "💬 Вы начали диалог с менеджером.\n"
        "Напишите ваш вопрос, и мы ответим в ближайшее время.",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "qr_payment", StateFilter('*'))
async def start_qr_payment(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "📸 Отправьте фото QR-кода или скриншот оплаты:"
    )
    await state.set_state(ServiceStates.waiting_for_photo)
    await callback.answer()


@router.message(ServiceStates.waiting_for_photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=file_id, photo_type="photo")
    
    await message.answer(
        "📝 Теперь введите сумму и описание (например: '1000 RUB, оплата за тур'):"
    )
    await state.set_state(ServiceStates.waiting_for_description)


@router.message(ServiceStates.waiting_for_photo, F.document)
async def process_document(message: Message, state: FSMContext):
    doc = message.document
    
    if doc.mime_type and doc.mime_type.startswith("image/"):
        file_id = doc.file_id
        await state.update_data(photo_file_id=file_id, photo_type="document")
        
        await message.answer(
            "📝 Теперь введите сумму и описание (например: '1000 RUB, оплата за тур'):"
        )
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
async def process_description(message: Message, state: FSMContext, bot):
    user_id = message.from_user.id
    username = message.from_user.username or "Без username"
    
    data = await state.get_data()
    photo_file_id = data.get("photo_file_id")
    photo_type = data.get("photo_type", "photo")
    description = message.text
    
    await state.update_data(
        description=description,
        username=username
    )
    
    if photo_type == "document":
        await bot.send_document(
            ADMIN_ID,
            photo_file_id,
            caption=f"💳 НОВАЯ ЗАЯВКА НА ОПЛАТУ СЕРВИСА\n"
                    f"Клиент: @{username} (ID: {user_id})\n"
                    f"Запрос: {description}",
            reply_markup=get_service_request_keyboard(user_id)
        )
    else:
        await bot.send_photo(
            ADMIN_ID,
            photo_file_id,
            caption=f"💳 НОВАЯ ЗАЯВКА НА ОПЛАТУ СЕРВИСА\n"
                    f"Клиент: @{username} (ID: {user_id})\n"
                    f"Запрос: {description}",
            reply_markup=get_service_request_keyboard(user_id)
        )
    
    await message.answer(
        "✅ Заявка отправлена менеджерам. Ожидайте подтверждения!",
        reply_markup=get_main_keyboard()
    )
    
    await state.clear()
