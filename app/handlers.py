from aiogram import html, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from datetime import datetime
from dateutil.relativedelta import relativedelta

import app.database.requests as rq
import app.keyboards as kb
from app.backend_api import BackendAPIError, get_config, get_my_wg_clients, get_qr


router = Router()


class Register(StatesGroup):
    name = State()


class Date(StatesGroup):
    tg_id = State()
    date = State()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
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
                         "/install_info - информация об установке сервиса на различные устройства\n"
                         "/faq - часто задаваемые вопросы\n"
                         "/profile - посмотреть профиль\n"
                         "/set_notif_one_time - установить разовое уведомление, которое сработает 1 раз\n"
                         "/del_notification - отключение разового уведомления\n"
                         "/switch_notif_mod - вкл/выкл авто-уведомлений (1-е число каждого месяца)")


@router.message(Command('info'))
async def cmd_info(message: Message) -> None:
    await message.answer(f"🗂 Стоимость за использование нашим впн-сервисом составляет 150р/мес. "
                         f"Если перевода не будет в течении недели, то мы посчитаем, "
                         f"что данным продуктом вы не планируете пользоваться. "
                         f"Следовательно вас придётся отключить.\n\n"
                         f"⬛️  Т-Банк (Тинькофф) 🟨\n"
                         f"Номер карты:\n"
                         f"{html.code('2200701392412133')}\n"
                         f"{html.code('Сафин Павел Римович')}\n"
                         f"(Кликабельный текст)\n\n"
                         f"Или по номеру телефона:\n"
                         f"+79805104653\n\n"
                         f"❓Если возникли вопросы, то пишите следующим лицам:\n"
                         f"@johnblec (Павел)\n"
                         f"@supremex3000 (Сергей)")


@router.message(Command('install_info'))
async def cmd_install_info(message: Message) -> None:
    await message.answer(f"✍️ Инструкция по установке ВПН на устройства:\n"
                         f"1. Скачиваем WireGuard на устройство (ПК, андроид, айфон);\n\n"
                         f"💻 ПК: {html.link('СКАЧАТЬ', 'https://download.wireguard.com/windows-client/wireguard-installer.exe')}\n"
                         f"📱 Android: {html.link('ССЫЛКА', 'https://play.google.com/store/apps/details?id=com.wireguard.android')}\n"
                         f"🖱 IOS (iphone): {html.link('ССЫЛКА', 'https://itunes.apple.com/us/app/wireguard/id1441195209?ls=1&mt=8')}\n\n"
                         f"2. Создаём туннель, отсканировав QR-код или загрузив файл конфигурации;\n\n"
                         f"3. Готово к использованию.\n\n"
                         f"❔Если возникли вопросы, то пишите:\n"
                         f"@johnblec (Павел)\n"
                         f"@supremex3000 (Сергей)")


@router.message(Command('faq'))
async def cmd_faq(message: Message) -> None:
    await message.answer(f"FAQ:\n\n"
                         f"{html.blockquote('Откуда мне взять QR-код или файл для создания туннеля?')}\n"
                         f"Их можно получить, обратившись к @johnblec или @supremex3000\n\n"
                         f"{html.blockquote('Если я пользуюсь ВПН на телефоне и хочу на комп себе, то нужно за это отдельно платить?')}\n"
                         f"Нет. Вы платите за весь ВПН фиксированную цену и можете пользоваться услугой на всех своих устройствах.\n\n"
                         f"{html.blockquote('Если сервис перестанет работать (заблокируют в России), оставшиеся месяц(-ы) использования сгорит(-ят)?')}\n"
                         f"Нет. С учётом пройденных дней использования сервисом вычтем и вернём деньги.\n\n"
                         f"Например, оплатили на 3 месяца. Через 1,5 месяца заблокировали сервис.\n"
                         f"450р - (150+75) = 225р\n"
                         f"225 рублей вернём.")


@router.message(Command('profile'))
async def cmd_profile(message: Message) -> None:
    u = await rq.get_user(message.from_user.id)
    if u:
        data = await rq.get_payment_term(u.tg_id)
        if data:
            for u, t in data:
                await message.answer(await norif_message(u, t))
        else:
            await message.answer(await norif_message(u))
    else:
        await message.answer(f"Произошла ошибка! Попробуйте позже или свяжитесь с разработчиков @johnblec")


async def norif_message(user, term=False) -> str:
    message = f"Данные вашего профиля:\n\n" + \
              f"ID: {user.tg_id}\n" + \
              f"Имя в боте: {user.name}\n"
    if term:
        message += f"Дата окончания подписки: {str(term.end_time).split()[0]}\n"
    if user.notif:
        return message + f"Авто-уведомления: Вкл"
    else:
        return message + f"Авто-уведомления: Выкл"


@router.message(Command('chname'))
async def cmd_chname(message: Message, state: FSMContext) -> None:
    await state.set_state(Register.name)
    await message.answer("Введите свои фамилию и инициалы (шаблон, Иванов И.):")


@router.message(Command('del_notification'))
async def cmd_del_notif(message: Message) -> None:
    result = await rq.get_payment_term(message.from_user.id)
    if result:
        for u, t in result:
            await rq.set_active_pay_term(t.id)
            await message.answer("Оповещение выключено")
    else:
        await message.answer("На данный момент у вас нет активных оповещений.")


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


@router.message(Command('set_notif_one_time'))
async def cmd_set_notif_one_time(message: Message, state: FSMContext) -> None:
    await state.set_state(Date.date)
    await state.update_data(date='', tg_id=message.from_user.id)
    await message.answer("Когда вы оформили подписку?", reply_markup=kb.start_date)


@router.message(Command('switch_notif_mod'))
async def cmd_switch_notif_mod(message: Message) -> None:
    await rq.update_user_notif(tg_id=message.from_user.id)
    user = await rq.get_user(message.from_user.id)
    if user.notif:
        await message.answer("Включен режим ежемесячного уведомления")
    else:
        await message.answer("Выключен режим ежемесячного уведомления")


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




def _format_subscription(subscription: dict) -> str:
    if not subscription:
        return "Подписка: не найдена"
    end_date = subscription.get("current_period_end") or "—"
    status_label = subscription.get("status_label") or subscription.get("status") or "—"
    access = "есть" if subscription.get("has_access") else "нет"
    return f"Подписка: {status_label}\nДата окончания: {end_date}\nДоступ по подписке: {access}"


def _format_wg_clients(data: dict) -> str:
    customer = data.get("customer") or {}
    clients = data.get("wg_clients") or []
    lines = ["🔐 Ваши VPN-клиенты"]
    if customer.get("real_name"):
        lines.append(f"Клиент: {customer['real_name']}")
    lines.append("")
    lines.append(_format_subscription(data.get("subscription") or {}))
    lines.append("")
    if not clients:
        lines.append("WG-клиенты пока не привязаны к вашему Telegram ID.")
        return "\n".join(lines)
    for idx, client in enumerate(clients, start=1):
        has_access = bool(client.get("has_vpn_access"))
        access_text = "✅ доступ есть" if has_access else "❌ доступа нет"
        reason = client.get("unavailable_reason") or ""
        lines.append(f"{idx}. {client.get('wg_name') or 'WG-клиент'}")
        if client.get("server_name"):
            lines.append(f"   Сервер: {client['server_name']}")
        lines.append(f"   VPN: {access_text}")
        if reason:
            lines.append(f"   Причина: {reason}")
    return "\n".join(lines)


@router.message(Command('my_vpn'))
async def cmd_my_vpn(message: Message) -> None:
    try:
        data = await get_my_wg_clients(message.from_user.id)
    except BackendAPIError as exc:
        await message.answer(f"Не удалось получить данные VPN: {exc}")
        return
    clients = data.get("wg_clients") or []
    reply_markup = kb.wg_clients_keyboard(clients) if clients else None
    await message.answer(_format_wg_clients(data), reply_markup=reply_markup)


@router.message(Command('my_config'))
async def cmd_my_config(message: Message) -> None:
    try:
        data = await get_my_wg_clients(message.from_user.id)
    except BackendAPIError as exc:
        await message.answer(f"Не удалось получить список VPN-клиентов: {exc}")
        return
    clients = data.get("wg_clients") or []
    if not clients:
        await message.answer("WG-клиенты пока не привязаны к вашему Telegram ID.")
        return
    await message.answer("Выберите WG-клиент, для которого нужен файл конфигурации:", reply_markup=kb.wg_clients_keyboard(clients))


@router.message(Command('my_qr'))
async def cmd_my_qr(message: Message) -> None:
    try:
        data = await get_my_wg_clients(message.from_user.id)
    except BackendAPIError as exc:
        await message.answer(f"Не удалось получить список VPN-клиентов: {exc}")
        return
    clients = data.get("wg_clients") or []
    if not clients:
        await message.answer("WG-клиенты пока не привязаны к вашему Telegram ID.")
        return
    await message.answer("Выберите WG-клиент, для которого нужен QR-код:", reply_markup=kb.wg_clients_keyboard(clients))


@router.callback_query(F.data.startswith('vpn_config:'))
async def cb_vpn_config(callback: CallbackQuery) -> None:
    await callback.answer()
    client_id = int(callback.data.split(':', 1)[1])
    try:
        file = await get_config(callback.from_user.id, client_id)
    except BackendAPIError as exc:
        await callback.message.answer(f"Не удалось выдать файл конфигурации: {exc}")
        return
    await callback.message.answer_document(
        BufferedInputFile(file.content, filename=file.filename),
        caption="Файл конфигурации WireGuard. Импортируйте его в приложение WireGuard."
    )


@router.callback_query(F.data.startswith('vpn_qr:'))
async def cb_vpn_qr(callback: CallbackQuery) -> None:
    await callback.answer()
    client_id = int(callback.data.split(':', 1)[1])
    try:
        file = await get_qr(callback.from_user.id, client_id)
    except BackendAPIError as exc:
        await callback.message.answer(f"Не удалось выдать QR-код: {exc}")
        return
    await callback.message.answer_document(
        BufferedInputFile(file.content, filename=file.filename),
        caption="QR-код WireGuard. Откройте WireGuard → добавить туннель → сканировать QR."
    )

@router.message()
async def echo_handler(message: Message) -> None:
    try:
        await message.answer("Я ничего не понял(\nВоспользуйтесь готовыми командами.")
    except TypeError:
        await message.answer("Хорошая попытка!)")
