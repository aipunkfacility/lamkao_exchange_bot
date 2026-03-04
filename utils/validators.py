from decimal import Decimal, InvalidOperation, getcontext, ROUND_HALF_UP
from typing import Union

# Set precision for financial calculations (28 digits is more than enough)
getcontext().prec = 28
getcontext().rounding = ROUND_HALF_UP


def clean_decimal(text: str) -> Decimal | None:
    """Валидирует и преобразует текст в Decimal с абсолютной точностью.

    Поддерживает:
    - Запятые как разделители: "1,5" -> Decimal('1.5')
    - Пробелы: "1 000" -> Decimal('1000')
    - Обычные точки: "1.5" -> Decimal('1.5')

    Returns:
        Decimal | None: Валидное число больше 0 или None, если невалидно.
    """
    if not text:
        return None

    cleaned = text.strip().replace(" ", "").replace(",", ".")

    try:
        value = Decimal(cleaned)
        return value if value > Decimal('0') else None
    except (InvalidOperation, ValueError):
        return None


def decimal_to_int_safe(value: Union[Decimal, float, int, str]) -> int:
    """Конвертирует Decimal/float/int в int с корректным округлением.
    
    Использует ROUND_HALF_UP для финансовых операций.
    Безопасно обрабатывает float -> Decimal преобразование.
    """
    if isinstance(value, (int, bool)):
        return int(value)
    
    if isinstance(value, str):
        try:
            value = Decimal(value)
        except InvalidOperation:
            raise ValueError(f"Cannot convert string '{value}' to Decimal")
    
    if isinstance(value, float):
        # Преобразуем float в строку чтобы избежать ошибок округления
        value = Decimal(str(value))
    
    if isinstance(value, Decimal):
        # Округляем до целого с ROUND_HALF_UP
        return int(value.to_integral_value(rounding=ROUND_HALF_UP))
    
    raise TypeError(f"Unsupported type: {type(value)}")
