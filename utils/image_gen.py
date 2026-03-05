from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from aiogram.types import BufferedInputFile

def generate_pin_image(pin_code: str, vnd_amount: int) -> BufferedInputFile:
    """
    Генерирует минималистичное изображение только с PIN-кодом и суммой.
    """
    width, height = 700, 350
    # Яркий фон LamKao
    img = Image.new("RGB", (width, height), "#FFCC00")
    draw = ImageDraw.Draw(img)
    
    # Форматируем сумму с пробелами (например: 149 850)
    formatted_amount = f"{vnd_amount:,}".replace(',', ' ')
    
    # Оставляем строго КОД и СУММУ (каждая с новой строки)
    text = f"{pin_code}\n{formatted_amount} VND"
    
    # Пытаемся загрузить шрифт
    try:
        # Увеличили размер шрифта до 100, так как лишних слов больше нет
        font = ImageFont.truetype("arial.ttf", 80)
    except OSError:
        font = ImageFont.load_default()

    # СОВРЕМЕННЫЙ МЕТОД для многострочного текста
    bbox = draw.multiline_textbbox((0, 0), text, font=font, align="center")
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Центрируем строго посередине
    x = (width - text_width) / 2
    y = (height - text_height) / 2
    
    # Рисуем текст
    draw.multiline_text((x, y), text, fill="black", font=font, align="center")
    
    img_bytes = BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    
    return BufferedInputFile(img_bytes.read(), filename=f"pin_{pin_code}.png")