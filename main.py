import asyncio
from aiogram import Bot, Dispatcher
from app.handlers import router
from app.config import settings

async def main():
    bot = Bot(token=settings.tg_api_token)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except:
        print("Бот выключен")