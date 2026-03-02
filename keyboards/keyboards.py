from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

# Создаем фабрику callback-данных
class ServiceCallback(CallbackData, prefix="srv"):
    action: str
    user_id: int

def get_main_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обменять валюту", callback_data="buy_vnd")
    builder.button(text="💳 Оплатить сервис / QR", callback_data="qr_payment")
    builder.button(text="❓ Связаться с менеджером", callback_data="ask_manager")
    builder.adjust(1)
    return builder.as_markup()

def get_service_action_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура управления заявкой для Админа"""
    builder = InlineKeyboardBuilder()
    # Используем фабрику
    builder.button(text="💰 Выставить счет", callback_data=ServiceCallback(action="bill", user_id=user_id))
    builder.button(text="💬 Написать / Ответить", callback_data=ServiceCallback(action="reply", user_id=user_id))
    builder.button(text="❌ Отклонить", callback_data=ServiceCallback(action="reject", user_id=user_id))
    builder.adjust(1)
    return builder.as_markup()

def get_chat_keyboard() -> InlineKeyboardMarkup:
    """Кнопка выхода из чата для клиента"""
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Завершить чат", callback_data="stop_chat")
    return builder.as_markup()

# Остальные клавиатуры (get_currency_keyboard и т.д.) оставь как были, если они используются