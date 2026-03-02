from os import getenv
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = getenv("BOT_TOKEN", "")
ADMIN_ID = int(getenv("ADMIN_ID") or 0)

RATES = {
    "RUB": 270,
    "USDT": 25500,
    "USD_CASH": 25400,
}

CURRENCY_NAMES = {
    "RUB": "Рубли (Безнал)",
    "USDT": "USDT",
    "USD_CASH": "Наличные Доллары",
}

ADMIN_CARD = "1111 2222 3333 4444"
