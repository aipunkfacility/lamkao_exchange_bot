def clean_float(text: str) -> float | None:
    """Валидирует и преобразует текст в float.

    Поддерживает:
    - Запятые как разделители: "1,5" -> 1.5
    - Пробелы: "1 000" -> 1000.0
    - Обычные точки: "1.5" -> 1.5

    Returns:
        float | None: Валидное число больше 0 или None, если невалидно.
    """
    if not text:
        return None

    cleaned = text.strip().replace(" ", "").replace(",", ".")

    try:
        value = float(cleaned)
        return value if value > 0 else None
    except ValueError:
        return None
