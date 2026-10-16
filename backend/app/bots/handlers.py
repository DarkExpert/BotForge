from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.db import async_session
from app.i18n.translations import translate
from app.services.records import get_or_create_user, record_activity, set_language


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="English", callback_data="language:en"),
                InlineKeyboardButton(text="العربية", callback_data="language:ar"),
            ]
        ]
    )


def create_router() -> Router:
    router = Router()

    @router.message(CommandStart())
    async def start(message: Message, bot_id: int, bot_username: str) -> None:
        if message.from_user is None:
            return
        async with async_session() as session:
            user = await get_or_create_user(session, bot_id, message.from_user.id, message.from_user.full_name)
            await record_activity(session, bot_id, user.id, "start", "User started the bot")
            language = user.language_code
        await message.answer(translate(language, "welcome", username=bot_username))

    @router.message(Command("language"))
    async def language(message: Message, bot_id: int) -> None:
        if message.from_user is None:
            return
        async with async_session() as session:
            user = await get_or_create_user(session, bot_id, message.from_user.id, message.from_user.full_name)
            language = user.language_code
        await message.answer(translate(language, "language_selection"), reply_markup=language_keyboard())

    @router.callback_query(F.data.in_({"language:en", "language:ar"}))
    async def change_language(callback: CallbackQuery, bot_id: int) -> None:
        chosen = callback.data.split(":", 1)[1]
        async with async_session() as session:
            user = await get_or_create_user(session, bot_id, callback.from_user.id, callback.from_user.full_name)
            await set_language(session, user, chosen)
            await record_activity(session, bot_id, user.id, "language_updated", "User changed language")
        await callback.answer()
        if isinstance(callback.message, Message):
            await callback.message.answer(translate(chosen, "language_updated"))

    @router.message(Command("help"))
    async def help_command(message: Message, bot_id: int) -> None:
        if message.from_user is None:
            return
        async with async_session() as session:
            user = await get_or_create_user(session, bot_id, message.from_user.id, message.from_user.full_name)
            language = user.language_code
        await message.answer(translate(language, "help"))

    @router.message(F.text)
    async def unsupported(message: Message, bot_id: int) -> None:
        if message.from_user is None:
            return
        async with async_session() as session:
            user = await get_or_create_user(session, bot_id, message.from_user.id, message.from_user.full_name)
            language = user.language_code
        await message.answer(translate(language, "unsupported"))

    return router
