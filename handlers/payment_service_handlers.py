from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID
from keyboards.keyboards import get_main_keyboard, get_service_request_keyboard
from states.states import ServiceStates

router = Router()


@router.callback_query(F.data == "qr_payment")
async def start_qr_payment(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📸 Отправьте фото QR-кода или скриншот оплаты:"
    )
    await state.set_state(ServiceStates.waiting_for_photo)
    await callback.answer()


@router.message(ServiceStates.waiting_for_photo)
async def process_photo(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("Пожалуйста, отправьте фото. Нажмите /cancel для отмены.")
        return
    
    file_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=file_id)
    
    await message.answer(
        "📝 Теперь введите сумму и описание (например: '1000 RUB, оплата за тур'):"
    )
    await state.set_state(ServiceStates.waiting_for_description)


@router.message(ServiceStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext, bot):
    user_id = message.from_user.id
    username = message.from_user.username or "Без username"
    
    data = await state.get_data()
    photo_file_id = data.get("photo_file_id")
    description = message.text
    
    await state.update_data(
        description=description,
        username=username
    )
    
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


@router.message(ServiceStates.waiting_for_photo, Command("cancel"))
@router.message(ServiceStates.waiting_for_description, Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Отменено. Выберите операцию:",
        reply_markup=get_main_keyboard()
    )
