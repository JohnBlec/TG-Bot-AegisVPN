import asyncio
import logging
import sys
import os

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from aiogram.filters import Command

from app.handlers import router, notification
from app.database.models import async_main


load_dotenv()
bot = Bot(token=os.getenv('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

scheduler = AsyncIOScheduler()


async def send_scheduled_message(chat_id: int, text: str):
    try:
        await bot.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения: {e}")


@dp.message(Command('schedule'))
async def schedule_message_handler(message: types.Message):
    """
    Обрабатывает команду /schedule для планирования сообщения.
    Пример команды: /schedule 2024-12-25 18:30 Поздравляю с Рождеством!
    """
    try:
        # Парсим аргументы команды
        args = message.text.split(maxsplit=3)
        if len(args) < 4:
            await message.reply("Использование: /schedule <YYYY-MM-DD> <HH:MM> <текст сообщения>")
            return

        date_str, time_str, text = args[1], args[2], args[3]
        send_time = f"{date_str} {time_str}"

        from datetime import datetime
        send_datetime = datetime.strptime(send_time, '%Y-%m-%d %H:%M')

        scheduler.add_job(
            send_scheduled_message,
            trigger=DateTrigger(run_date=send_datetime),
            args=[message.chat.id, text]
        )

        await message.reply(f"Сообщение запланировано на {send_datetime}.")
    except ValueError:
        await message.reply("Ошибка: проверьте формат даты и времени. Использование: /schedule <YYYY-MM-DD> <HH:MM> <текст сообщения>")
    except Exception as e:
        logging.error(f"Ошибка в обработчике: {e}")
        await message.reply("Произошла ошибка при попытке запланировать сообщение.")


async def main() -> None:
    await async_main()
    dp.include_router(router)
    scheduler.add_job(
        notification,
        'cron', hour=8, minute=0
    )
    scheduler.start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Finish Bot')
