import asyncio
import logging
from aiogram import Dispatcher, Bot
from aiogram_sqlite_storage.sqlitestore import SQLStorage
from aiogram.types import BotCommand

from config import BOT_TOKEN
from database.db import init_db, async_session
from middlewares.db_middleware import DbSessionMiddleware
from handlers.user_handlers import router as user_router
from handlers.admin_handlers import router as admin_router
from handlers.payment_service_handlers import router as payment_service_router

logging.basicConfig(level=logging.INFO)


async def on_startup(bot: Bot):
    commands = [
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="rates", description="💱 Актуальный курс валют"),
        BotCommand(command="cancel", description="❌ Отмена текущее действие"),
        BotCommand(command="help", description="ℹ️ Информация и контакты"),
    ]
    await bot.set_my_commands(commands)


async def main():
    bot = Bot(token=BOT_TOKEN)
    storage = SQLStorage("fsm_storage.db")
    dp = Dispatcher(storage=storage)
    
    dp.update.middleware(DbSessionMiddleware(session_pool=async_session))
    
    await init_db()
    
    dp.include_router(payment_service_router)
    dp.include_router(user_router)
    dp.include_router(admin_router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await on_startup(bot)
    
    try:
        await dp.start_polling(bot)
    finally:
        await storage.close()

if __name__ == "__main__":
    asyncio.run(main())
