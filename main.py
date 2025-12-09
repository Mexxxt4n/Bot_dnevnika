import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import TOKEN
from app.hand import router
from notifications import check_and_send_homework_reminders

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    dp.include_router(router)
    # 🔧 запускаем уведомления параллельно
    asyncio.create_task(check_and_send_homework_reminders())
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
