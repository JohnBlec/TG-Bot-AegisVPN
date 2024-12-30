from aiogram import html, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from datetime import datetime
from dateutil.relativedelta import relativedelta

import app.database.requests as rq
import app.keyboards as kb


router = Router()


class Register(StatesGroup):
    name = State()


class Date(StatesGroup):
    tg_id = State()
    date = State()


@router.message(CommandStart())
async def command_start(message: Message) -> None:
    result = await rq.set_user(message.from_user.id, message.from_user.full_name)
    if not result:
        await message.answer(f"Извините! произошла какая-то ошибка.\nПопробуйте позже...")
        return
    await message.answer(f"👋 Приветствую, {html.bold(message.from_user.full_name)}!\n"
                         f"Если собираетесь использовать наш ВПН, "
                         f"то рекомендую сменить имя в боте с помощью команды /chname, "
                         f"чтобы мы могли индентифицировать. Спасибо 😊")


@router.message(Command('help'))
async def cmd_help(message: Message) -> None:
    await message.answer("📃 Список команд бота:\n\n"
                         "/chname - сменить имя в боте\n"
                         "/info - информация о сервисе (тарифы и оплата)\n"
                         "/profile - посмотреть профиль\n"
                         "/set_notification - установить уведомление для продления подписки")


@router.message(Command('profile'))
async def cmd_reg(message: Message) -> None:
    u = await rq.get_user(message.from_user.id)
    if u:
        await message.answer(f"Данные вашего профиля:\n\n"
                             f"ID: {u.tg_id}\n"
                             f"ТГ имя: {message.from_user.full_name}\n"
                             f"Имя в боте: {u.name}\n"
                             f"Статус подписки: {u.sub}")
    else:
        await message.answer(f"Произошла ошибка! Попробуйте позже или свяжитесь с разработчиков @johnblec")


@router.message(Command('chname'))
async def cmd_reg(message: Message, state: FSMContext) -> None:
    await state.set_state(Register.name)
    await message.answer("Введите свои фамилию и инициалы (шаблон, Иванов И.):")


@router.message(Register.name)
async def st_reg_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    data = await state.get_data()
    result = await rq.update_user_name(message.from_user.id, data["name"])
    if not result:
        await message.answer(f"Извините! произошла какая-то ошибка.\nПопробуйте позже...")
        return
    await message.reply(f'Имя изменено на {data["name"]}!')
    await state.clear()


@router.message(Command('set_notification'))
async def cmd_set_time(message: Message, state: FSMContext) -> None:
    await state.set_state(Date.date)
    await state.update_data(date='', tg_id=message.from_user.id)
    await message.answer("Когда вы оформили подписку?", reply_markup=kb.start_date)


@router.callback_query(F.data == 'now_date')
async def now_date(callback: CallbackQuery) -> None:
    await callback.answer('Выбран сегодняшний день')
    await callback.message.edit_text('Выбран сегодняшний день')
    await callback.message.answer('Выберите длительность подписки:', reply_markup=kb.months)


@router.callback_query(F.data == 'other_date')
async def other_date(callback: CallbackQuery) -> None:
    await callback.answer('Выбран другой день')
    await callback.message.edit_text('Выбран другой день')
    await callback.message.answer('Введите дату оплаты (Например, 11.11.2024):')


@router.message(Date.date)
async def st_date(message: Message, state: FSMContext) -> None:
    date_text = message.text
    if not date_text.replace('.', '').isdigit() or date_text.count('.') != 2:
        await message.reply("Некорректная дата. Убедитесь, "
                            "что вы вводите дату в формате ДД.ММ.ГГГГ и повторите попытку.")
        return
    try:
        validated_date = datetime.strptime(date_text, '%d.%m.%Y')
        if validated_date.date() > datetime.now().date():
            await message.reply(
                "Дата не может быть в будущем. Пожалуйста, введите корректную дату:")
            return
        await state.update_data(date=date_text)
        await message.reply(f'Выберите длительность подписки:', reply_markup=kb.months)
    except ValueError:
        await message.reply(
            "Некорректная дата. Убедитесь, что вы вводите дату в формате ДД.ММ.ГГГГ и повторите попытку.")


@router.callback_query(F.data == 'one_month')
async def one_month(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    result = await rq.set_payment_term(data["tg_id"], data["date"], 1)
    await set_date_func(callback, result, data["date"], data["tg_id"], 1)
    await state.clear()


@router.callback_query(F.data == 'three_month')
async def three_month(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    result = await rq.set_payment_term(data["tg_id"], data["date"], 3)
    await callback.answer('Подписка на 3 месяца', show_alert=True)
    await set_date_func(callback, result, data["date"], data["tg_id"], 3)
    await state.clear()


@router.callback_query(F.data == 'six_month')
async def six_month(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    result = await rq.set_payment_term(data["tg_id"], data["date"], 6)
    await callback.answer('Подписка на 6 месяцев', show_alert=True)
    await set_date_func(callback, result, data["date"], data["tg_id"], 6)
    await state.clear()


@router.callback_query(F.data == 'twelve_month')
async def twelve_month(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    result = await rq.set_payment_term(data["tg_id"], data["date"], 12)
    await callback.answer('Подписка на 12 месяцев', show_alert=True)
    await set_date_func(callback, result, data["date"], data["tg_id"], 12)
    await state.clear()


async def set_date_func(callback: CallbackQuery, result: bool, start_date: str, tg_id: int, count_months: int) -> None:
    if result:
        if start_date:
            d = datetime.strptime(start_date, '%d.%m.%Y')
        else:
            d = datetime.now().date()
        next_d = d + relativedelta(months=count_months)
        await callback.message.edit_text(f'Установлено уведомление к дате: {next_d}')
    else:
        data_rq = await rq.get_payment_term(tg_id)
        for user, date in data_rq:
            date, time = str(date.end_time).split()
            await callback.message.edit_text(f'У вас уже установлено уведомление на {date}')


@router.callback_query(F.data == 'cancel')
async def cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer('Отмена действия')
    await callback.message.edit_text('Операция отменена...')
    await state.clear()


@router.message()
async def echo_handler(message: Message) -> None:
    try:
        # Send a copy of the received message
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        # But not all the types is supported to be copied so need to handle it
        await message.answer("Nice try!")
