from aiogram import html, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

router = Router()


def notification():
    pass

@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Приветствую, {html.bold(message.from_user.full_name)}!")


@router.message(Command('help'))
async def cmd_help(message: Message) -> None:
    await message.answer(f"/start - начало программы\n/reg - регистрация в программе\n/info - информация о сервисе")


@router.message()
async def echo_handler(message: Message) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types (like a text, photo, sticker etc.)
    """
    try:
        # Send a copy of the received message
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        # But not all the types is supported to be copied so need to handle it
        await message.answer("Nice try!")