from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import CURRENCY_NAMES


def get_main_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Купить Донги (VND)", callback_data="buy_vnd")
    builder.button(text="Оплатить сервис/QR", callback_data="qr_payment")
    builder.button(text="❓ Связаться с менеджером", callback_data="ask_manager")
    builder.adjust(1)
    return builder.as_markup()


def get_currency_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, name in CURRENCY_NAMES.items():
        builder.button(text=name, callback_data=f"currency:{code}")
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm_exchange")
    builder.button(text="🔙 Назад", callback_data="back_to_amount")
    builder.adjust(2)
    return builder.as_markup()


def get_payment_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🧾 Я оплатил", callback_data="user_paid")
    return builder.as_markup()


def get_admin_order_keyboard(user_id: int, amount_display: str, amount_vnd: int, username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    amount_for_callback = amount_display.replace(" ", "_")
    builder.button(
        text="✅ Одобрить (Дать реквизиты)",
        callback_data=f"approve:{user_id}:{amount_for_callback}:{amount_vnd}:{username}"
    )
    builder.button(
        text="❌ Отклонить",
        callback_data=f"reject:{user_id}"
    )
    builder.adjust(2)
    return builder.as_markup()


def get_admin_payment_confirm_keyboard(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Деньги пришли",
        callback_data=f"payment_confirmed:{user_id}"
    )
    return builder.as_markup()


def get_chat_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Завершить чат", callback_data="stop_chat")
    return builder.as_markup()


def get_admin_chat_keyboard(client_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="💬 Ответить клиенту",
        callback_data=f"chat_reply:{client_id}"
    )
    builder.button(
        text="❌ Завершить чат с этим клиентом",
        callback_data=f"chat_end:{client_id}"
    )
    builder.adjust(2)
    return builder.as_markup()
