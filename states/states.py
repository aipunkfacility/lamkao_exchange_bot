from aiogram.fsm.state import State, StatesGroup


class ExchangeStates(StatesGroup):
    select_currency = State()
    enter_amount = State()
    confirm_exchange = State()
    waiting_payment = State()


class PaymentServiceStates(StatesGroup):
    waiting_photo = State()
    waiting_description = State()


class ChatStates(StatesGroup):
    in_chat = State()


class AdminChat(StatesGroup):
    replying_to_user = State()
