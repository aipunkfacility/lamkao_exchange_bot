from aiogram.fsm.state import State, StatesGroup

class ExchangeStates(StatesGroup):
    """Состояния для процесса обмена валюты"""
    choosing_currency = State()
    entering_amount = State()
    confirming = State()

class ChatStates(StatesGroup):
    """Состояния для чата с менеджером"""
    in_chat = State()

class ServiceStates(StatesGroup):
    """Состояния для модуля оплаты сервисов (бургеры, визы и т.д.)"""
    waiting_for_photo = State()
    waiting_for_description = State()

class AdminStates(StatesGroup):
    """Состояния для действий администратора"""
    waiting_for_service_amount = State() # Ожидание ввода суммы счета для сервиса
    waiting_for_service_result = State()  # Ожидание отправки результата (чек/билет/код) клиенту

class AdminChat(StatesGroup):
    """Состояния для чата со стороны администратора"""
    replying_to_user = State()