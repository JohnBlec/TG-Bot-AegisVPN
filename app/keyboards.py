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



def wg_clients_keyboard(clients: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for client in clients:
        client_id = client.get("id")
        name = client.get("wg_name") or f"WG #{client_id}"
        rows.append([InlineKeyboardButton(text=f"📄 Файл: {name}", callback_data=f"vpn_config:{client_id}")])
        rows.append([InlineKeyboardButton(text=f"📲 QR: {name}", callback_data=f"vpn_qr:{client_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
