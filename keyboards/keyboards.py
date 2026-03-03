from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

# Фабрика для обработки кнопок сервиса
class ServiceCallback(CallbackData, prefix="srv"):
    action: str
    user_id: int

# Фабрика для обработки кнопок обмена валют
class ExchangeCallback(CallbackData, prefix="exc"):
    action: str
    user_id: int
    amount: str
    currency: str
    vnd_amount: int

def get_main_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обменять валюту", callback_data="buy_vnd", style="primary")
    builder.button(text="💳 Оплатить сервис / QR", callback_data="qr_payment", style="primary")
    builder.button(text="❓ Связаться с менеджером", callback_data="ask_manager", style="primary")
    builder.adjust(1)
    return builder.as_markup()

def get_currency_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # Эти коды должны совпадать с ключами в config.RATES
    builder.button(text="Рубли (РФ Банки)", callback_data="currency:RUB", style="primary")
    builder.button(text="USDT / Крипта", callback_data="currency:USDT", style="primary")
    builder.button(text="Наличные USD", callback_data="currency:USD", style="primary")
    builder.button(text="🔙 Назад", callback_data="back_to_menu", style="primary")
    builder.adjust(1)
    return builder.as_markup()

def get_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm_exchange", style="success")
    builder.button(text="❌ Отмена", callback_data="back_to_menu", style="danger")
    builder.adjust(2)
    return builder.as_markup()

# Та самая функция, которую искал бот:
def get_service_request_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для ПЕРВИЧНОЙ заявки на сервис (для Админа)"""
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Выставить счет", callback_data=ServiceCallback(action="bill", user_id=user_id), style="success")
    builder.button(text="💬 Уточнить детали", callback_data=ServiceCallback(action="reply", user_id=user_id), style="primary")
    builder.button(text="❌ Отклонить", callback_data=ServiceCallback(action="reject", user_id=user_id), style="danger")
    builder.adjust(1)
    return builder.as_markup()

def get_service_action_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для ПОСЛЕДУЮЩИХ действий в чате (для Админа)"""
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Выставить счет", callback_data=ServiceCallback(action="bill", user_id=user_id), style="success")
    builder.button(text="💬 Написать еще", callback_data=ServiceCallback(action="reply", user_id=user_id), style="primary")
    builder.button(text="❌ Завершить", callback_data=ServiceCallback(action="reject", user_id=user_id), style="danger")
    builder.adjust(1)
    return builder.as_markup()

def get_chat_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Завершить чат", callback_data="stop_chat", style="danger")
    return builder.as_markup()

# --- ПРОПУЩЕННЫЕ КЛАВИАТУРЫ ДЛЯ ОБМЕНА ВАЛЮТЫ И ОПЛАТЫ ---

def get_admin_order_keyboard(user_id: int, amount_display: str, amount_vnd: int, username: str) -> InlineKeyboardMarkup:
    """Клавиатура для Админа: Новая заявка на обмен валюты"""
    builder = InlineKeyboardBuilder()
    amount_for_callback = amount_display.replace(" ", "_")
    
    # style="success" для одобрения (Liquid Glass)
    builder.button(
        text="✅ Одобрить (Дать реквизиты)",
        callback_data=f"approve:{user_id}:{amount_for_callback}:{amount_vnd}:{username}",
        style="success"
    )
    # style="danger" для отклонения (Liquid Glass)
    builder.button(
        text="❌ Отклонить",
        callback_data=f"reject:{user_id}",
        style="danger"
    )
    builder.adjust(1)
    return builder.as_markup()

def get_payment_confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для Клиента: Подтверждение оплаты (Обмен)"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🧾 Я оплатил", callback_data="user_paid", style="success")
    return builder.as_markup()

def get_admin_payment_confirm_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для Админа: Подтверждение прихода денег (Обмен)"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Деньги пришли",
        callback_data=f"payment_confirmed:{user_id}",
        style="success"
    )
    return builder.as_markup()

def get_service_payment_keyboard(amount: int) -> InlineKeyboardMarkup:
    """Клавиатура для Клиента: Подтверждение оплаты (Сервис/Счет)"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🧾 Я оплатил", 
        callback_data=f"service_paid:{amount}", 
        style="success"
    )
    return builder.as_markup()

# --- КЛАВИАТУРЫ ДЛЯ ОБМЕНА ВАЛЮТЫ ---

def get_exchange_keyboard(user_id: int, amount: str, currency: str, vnd_amount: int) -> InlineKeyboardMarkup:
    """Клавиатура для Админа: Обработка заявки на обмен валюты"""
    builder = InlineKeyboardBuilder()
    
    # style="success" для одобрения (Liquid Glass)
    builder.button(
        text="✅ Одобрить", 
        callback_data=ExchangeCallback(action="approve", user_id=user_id, amount=amount, currency=currency, vnd_amount=vnd_amount),
        style="success"
    )
    # style="primary" для уточнения деталей (Liquid Glass)
    builder.button(
        text="💬 Уточнить детали", 
        callback_data=ExchangeCallback(action="chat", user_id=user_id, amount=amount, currency=currency, vnd_amount=vnd_amount),
        style="primary"
    )
    # style="danger" для отклонения (Liquid Glass)
    builder.button(
        text="❌ Отклонить", 
        callback_data=ExchangeCallback(action="reject", user_id=user_id, amount=amount, currency=currency, vnd_amount=vnd_amount),
        style="danger"
    )
    builder.adjust(1)
    return builder.as_markup()