from aiogram import html, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import app.database.requests as rq
import app.keyboards as kb


router = Router()


class Register(StatesGroup):
    name = State()


class Date(StatesGroup):
    date = State()


def notification():
    pass


@router.message(CommandStart())
async def command_start(message: Message) -> None:
    await rq.set_user(message.from_user.id, message.from_user.full_name)
    await message.answer(f"Приветствую, {html.bold(message.from_user.full_name)}!")


@router.message(Command('help'))
async def cmd_help(message: Message) -> None:
    await message.answer("/reg - регистрация\n/info - информация о сервисе")


@router.message(Command('reg'))
async def cmd_reg(message: Message, state: FSMContext) -> None:
    await state.set_state(Register.name)
    await message.answer("Введите свои фамилию и инициалы (шаблон, Иванов И.):")


@router.message(Register.name)
async def st_reg_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    data = await state.get_data()
    await rq.update_user_name(message.from_user.id, data["name"])
    await message.reply(f'Имя изменено на {data["name"]}!')


@router.message(Command('set_time'))
async def cmd_set_time(message: Message) -> None:
    await message.answer("Когда вы оформили подписку?", reply_markup=kb.start_date)


@router.callback_query(F.data == 'now_date')
async def now_date(callback: CallbackQuery):
    await callback.answer('Выбран сегодняшний день')
    await callback.message.edit_text('Выбран сегодняшний день')
    await callback.message.answer('Выберите длительность подписки:', reply_markup=kb.months)


@router.callback_query(F.data == 'other_date')
async def other_date(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Выбран другой день')
    await callback.message.edit_text('Выбран другой день')
    await state.set_state(Date.date)
    await callback.message.answer('Введите дату оплаты:')


@router.message(Date.date)
async def st_date(message: Message, state: FSMContext) -> None:
    await state.update_data(date=message.text)
    data = await state.get_data()
    await rq.update_user_name(message.from_user.id, data["date"])
    await message.reply(f'Имя изменено на {data["date"]}!', reply_markup=kb.months)


@router.callback_query(F.data == 'one_month')
async def one_month(callback: CallbackQuery):
    await callback.answer('Подписка на 1 месяц', show_alert=True)
    await callback.message.edit_text('one_month')


@router.callback_query(F.data == 'three_month')
async def three_month(callback: CallbackQuery):
    await callback.answer('Подписка на 3 месяц', show_alert=True)
    await callback.message.edit_text('three_month')


@router.callback_query(F.data == 'six_month')
async def six_month(callback: CallbackQuery):
    await callback.answer('Подписка на 6 месяц', show_alert=True)
    await callback.message.edit_text('six_month')


@router.callback_query(F.data == 'twelve_month')
async def twelve_month(callback: CallbackQuery):
    await callback.answer('Подписка на 12 месяц', show_alert=True)
    await callback.message.edit_text('twelve_month')


@router.callback_query(F.data == 'cancel')
async def cancel(callback: CallbackQuery):
    await callback.answer('Отмена действия')
    await callback.message.edit_text('Операция отменена...')


"""@router.message()
async def echo_handler(message: Message) -> None:
    try:
        # Send a copy of the received message
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        # But not all the types is supported to be copied so need to handle it
        await message.answer("Nice try!")"""
