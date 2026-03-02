import asyncio
import logging
from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from handlers.user_handlers import router as user_router
from handlers.admin_handlers import router as admin_router
from handlers.payment_service_handlers import router as payment_service_router

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    dp.include_router(user_router)
    dp.include_router(admin_router)
    dp.include_router(payment_service_router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
