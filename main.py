import asyncio
from aiogram import Dispatcher
from logger import setup_logger
from dotenv import load_dotenv

from database.database import init_db
from handlers.start import bot, handlers_router, on_start
from handlers.iquery import query_router

async def main() -> None:
    setup_logger()

    dp = Dispatcher()
    dp.include_routers(handlers_router, query_router)
    
    init_db()  # Инициализация БД

    await on_start()
    await bot.delete_webhook(True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
