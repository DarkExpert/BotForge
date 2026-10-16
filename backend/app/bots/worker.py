import asyncio
import logging
import signal

from aiogram import Bot as TelegramBot, Dispatcher

from app.config import get_settings
from app.db import async_session, engine
from app.logging_config import configure_logging
from app.services.records import save_bot
from app.bots.handlers import create_router

logger = logging.getLogger(__name__)


async def resolve_identity(bot: TelegramBot) -> str:
    identity = await bot.get_me()
    if not identity.username:
        raise ValueError("Telegram bot has no username")
    return identity.username


async def run_bot(name: str, token: str, stop: asyncio.Event) -> None:
    try:
        bot = TelegramBot(token=token)
    except Exception:
        logger.error("Invalid bot configuration for %s", name)
        return
    try:
        while not stop.is_set():
            try:
                username = await resolve_identity(bot)
                async with async_session() as session:
                    record = await save_bot(session, name, username)
                dispatcher = Dispatcher()
                dispatcher.include_router(create_router())
                logger.info("Starting bot polling: %s", name)
                await dispatcher.start_polling(
                    bot, bot_id=record.id, bot_username=username,
                    handle_signals=False, close_bot_session=False,
                )
                if not stop.is_set():
                    logger.warning("Bot polling stopped unexpectedly: %s", name)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.error("Bot polling failed for %s; retrying", name)
            try:
                await asyncio.wait_for(stop.wait(), timeout=5)
            except TimeoutError:
                pass
    finally:
        await bot.session.close()


async def main() -> None:
    settings = get_settings()
    tokens = {
        "Alpha": settings.telegram_bot_alpha_token,
        "Beta": settings.telegram_bot_beta_token,
    }
    if any(not token for token in tokens.values()):
        raise SystemExit("Both Telegram bot tokens must be configured for bot-worker")
    if len(set(tokens.values())) != len(tokens):
        raise SystemExit("Bot tokens must identify different Telegram bots")

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    tasks = [asyncio.create_task(run_bot(name, token, stop)) for name, token in tokens.items()]
    try:
        await stop.wait()
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await engine.dispose()


if __name__ == "__main__":
    configure_logging()
    asyncio.run(main())
