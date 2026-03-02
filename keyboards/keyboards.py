from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import CURRENCY_NAMES

def get_main_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Купить Донги (VND)", callback_data="buy_vnd")
    builder.button(text="Оплатить сервис/QR", callback_data="qr_payment")
    builder.adjust(1)
    return builder.as_markup()


def get_currency_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, name in CURRENCY_NAMES.items():
        builder.button(text=name, callback_data=f"currency:{code}")
    builder.adjust(1)
    return builder.as_markup()


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm_exchange")
    builder.button(text="❌ Отменить", callback_data="cancel_exchange")
    builder.adjust(2)
    return builder.as_markup()


def get_payment_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🧾 Я оплатил", callback_data="user_paid")
    return builder.as_markup()


def get_admin_order_keyboard(user_id: int, amount_rub: int, amount_vnd: int, username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Одобрить (Дать реквизиты)",
        callback_data=f"approve:{user_id}:{amount_rub}:{amount_vnd}:{username}"
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
