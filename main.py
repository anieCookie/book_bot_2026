import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, BOOKS_DIR, QDRANT_PATH
from user_handlers import user_router
from db.database import init_db
from search.qdrant_service import init_qdrant_collection

os.makedirs(BOOKS_DIR, exist_ok=True)
os.makedirs(QDRANT_PATH, exist_ok=True)

logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(token=BOT_TOKEN)

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(user_router)
    await init_db()

    init_qdrant_collection()
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("BOT OFF")