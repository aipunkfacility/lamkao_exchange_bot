from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID
from keyboards.keyboards import get_main_keyboard
from states.states import PaymentServiceStates

router = Router()


@router.callback_query(F.data == "qr_payment")
async def start_qr_payment(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📸 Отправьте фото QR-кода или скриншот оплаты:"
    )
    await state.set_state(PaymentServiceStates.waiting_photo)
    await callback.answer()


@router.message(PaymentServiceStates.waiting_photo)
async def process_photo(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("Пожалуйста, отправьте фото. Нажмите /cancel для отмены.")
        return
    
    file_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=file_id)
    
    await message.answer(
        "📝 Теперь введите сумму и описание (например: '1000 RUB, оплата за тур'):"
    )
    await state.set_state(PaymentServiceStates.waiting_description)


@router.message(PaymentServiceStates.waiting_description)
async def process_description(message: Message, state: FSMContext, bot):
    user_id = message.from_user.id
    username = message.from_user.username or "Без username"
    
    data = await state.get_data()
    photo_file_id = data["photo_file_id"]
    description = message.text
    
    await bot.send_message(
        ADMIN_ID,
        f"💳 НОВАЯ ЗАЯВКА НА ОПЛАТУ СЕРВИСА\n"
        f"Клиент: @{username} (ID: {user_id})\n"
        f"Описание: {description}"
    )
    
    await bot.send_photo(
        ADMIN_ID,
        photo_file_id,
        caption=f"Фото от @{username}"
    )
    
    await message.answer(
        "✅ Заявка отправлена менеджерам. Ожидайте подтверждения!",
        reply_markup=get_main_keyboard()
    )
    
    await state.clear()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Отменено. Выберите операцию:",
        reply_markup=get_main_keyboard()
    )
