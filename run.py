import asyncio
import logging
import sys
import os

from dotenv import load_dotenv
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from app.handlers import router
from app.database.models import async_main
from app.database.requests import select_payment_terms as s_p_t, set_active_pay_term as set_act_p_t,\
    select_users, update_user_notif


load_dotenv()
bot = Bot(token=os.getenv('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

scheduler = AsyncIOScheduler()


async def send_scheduled_message(chat_id: int, text: str, pay_term_id: int = 0):
    try:
        await bot.send_message(chat_id=chat_id, text=text)
        if pay_term_id != 0:
            await set_act_p_t(pay_term_id)
        else:
            await update_user_notif(chat_id)
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения: {e}")


async def notification():
    try:
        u_s = await s_p_t()
        for user, pay_term in u_s:
            if pay_term.end_time.date() == datetime.now().date():
                send_time = f"{pay_term.end_time.date()} 12:00"
                text = 'Напоминаю, что сегодня нужно продлить подписку на ВПН!'
                send_datetime = datetime.strptime(send_time, '%Y-%m-%d %H:%M')
                scheduler.add_job(
                    send_scheduled_message,
                    trigger=DateTrigger(run_date=send_datetime),
                    args=[user.tg_id, text, pay_term.id]
                )
                logging.info(f"Уведомление установленно в {send_datetime} для {user.tg_id} подписки {pay_term.id}")
        logging.info(f"{u_s}")
    except ValueError as v:
        logging.error(f"Ошибка в обработчике: {v}")
    except Exception as e:
        logging.error(f"Ошибка в обработчике: {e}")


async def notification_every_month():
    try:
        s_u = await select_users()
        for user in s_u:
            send_time = f"{datetime.now().date()} 18:44"
            text = 'Напоминаю, что сегодня нужно продлить подписку на ВПН!'
            send_datetime = datetime.strptime(send_time, '%Y-%m-%d %H:%M')
            scheduler.add_job(
                send_scheduled_message,
                trigger=DateTrigger(run_date=send_datetime),
                args=[user.tg_id, text]
            )
            logging.info(f"Уведомление установленно в {send_datetime} для {user.tg_id}")
        logging.info(f"{s_u}")
    except ValueError as v:
        logging.error(f"Ошибка в обработчике: {v}")
    except Exception as e:
        logging.error(f"Ошибка в обработчике: {e}")


async def main() -> None:
    await async_main()
    dp.include_router(router)
    scheduler.add_job(
        notification_every_month,
        'cron', day=1, hour=9, minute=0
    )
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
