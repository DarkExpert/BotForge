from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models import Activity, Bot, BotUser


async def save_bot(session: AsyncSession, name: str, username: str) -> Bot:
    bot = await session.scalar(select(Bot).where(Bot.name == name))
    if bot is None:
        bot = Bot(name=name, username=username, is_active=True)
        session.add(bot)
    else:
        bot.username = username
        bot.is_active = True
    await session.commit()
    await session.refresh(bot)
    return bot


async def get_or_create_user(
    session: AsyncSession, bot_id: int, telegram_user_id: int, display_name: str
) -> BotUser:
    user = await session.scalar(
        select(BotUser).where(BotUser.bot_id == bot_id, BotUser.telegram_user_id == telegram_user_id)
    )
    if user is None:
        try:
            async with session.begin_nested():
                user = BotUser(bot_id=bot_id, telegram_user_id=telegram_user_id, display_name=display_name)
                session.add(user)
                await session.flush()
        except IntegrityError:
            user = await session.scalar(
                select(BotUser).where(BotUser.bot_id == bot_id, BotUser.telegram_user_id == telegram_user_id)
            )
            if user is None:
                raise
    if user.display_name != display_name:
        user.display_name = display_name
    await session.commit()
    await session.refresh(user)
    return user


async def set_language(session: AsyncSession, user: BotUser, language: str) -> None:
    user.language_code = language
    await session.commit()


async def record_activity(
    session: AsyncSession, bot_id: int, user_id: int | None, event_type: str, description: str
) -> None:
    session.add(Activity(bot_id=bot_id, user_id=user_id, event_type=event_type, description=description))
    await session.commit()
