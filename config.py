import os
from dotenv import load_dotenv

load_dotenv()

# Основные настройки из .env
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_ID: int = int(os.getenv("ADMIN_ID") or "0")
SBER_CARD: str = os.getenv("SBER_CARD", "Реквизиты не указаны")

# Курсы валют для демо (можно менять здесь)
RATES = {
    "RUB": 270,    # 1 рубль = 270 донгов
    "USDT": 25500, # 1 USDT = 25500 донгов
    "USD": 25400   # 1 USD = 25400 донгов
}

# Названия валют для кнопок
CURRENCY_NAMES = {
    "RUB": "Рубли (РФ Банки)",
    "USDT": "USDT / Крипта",
    "USD": "Наличные USD"
}