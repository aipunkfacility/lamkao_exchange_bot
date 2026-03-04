from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from aiogram.types import BufferedInputFile

def generate_pin_image(pin_code: str) -> BufferedInputFile:
    """
    Генерирует изображение с PIN-кодом, совместимое с современными версиями Pillow.
    """
    width, height = 600, 300
    img = Image.new("RGB", (width, height), "#FFCC00")
    draw = ImageDraw.Draw(img)
    
    text = f"PIN: {pin_code}"
    
    # Пытаемся загрузить шрифт, если не нашли - используем дефолтный
    try:
        font = ImageFont.truetype("arial.ttf", 80)
    except OSError:
        font = ImageFont.load_default()

    # СОВРЕМЕННЫЙ МЕТОД (вместо textsize)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (width - text_width) / 2
    y = (height - text_height) / 2
    
    draw.text((x, y), text, fill="black", font=font)
    
    img_bytes = BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    
    return BufferedInputFile(img_bytes.read(), filename="pin_code.png")