from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

start_date = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Сегодня', callback_data='now_date')],
    [InlineKeyboardButton(text='Другой день...', callback_data='other_date')],
    [InlineKeyboardButton(text='Отмена', callback_data='cancel')]
])

months = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='1 мес.', callback_data='one_month'),
     InlineKeyboardButton(text='3 мес.', callback_data='three_month')],
    [InlineKeyboardButton(text='6 мес.', callback_data='six_month'),
     InlineKeyboardButton(text='12 мес.', callback_data='twelve_month')],
    [InlineKeyboardButton(text='Отмена', callback_data='cancel')]
])


def wg_clients_keyboard(clients: list[dict], action: str) -> InlineKeyboardMarkup:
    rows = []
    for client in clients:
        client_id = client.get("id")
        name = client.get("wg_name") or f"WG #{client_id}"
        status = "🟢" if client.get("is_active") else "🔴"
        rows.append([InlineKeyboardButton(text=f"{status} {name}", callback_data=f"wg:{action}:{client_id}")])
    rows.append([InlineKeyboardButton(text="Отмена", callback_data="wg:cancel:0")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
