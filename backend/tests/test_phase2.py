import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.bots.worker import resolve_identity
from app.config import Settings, get_settings
from app.db import get_session
from app.main import app
from app.models import Activity, Base, BotUser
from app.services.records import get_or_create_user, record_activity, save_bot, set_language


def test_bot_identity_uses_telegram_get_me() -> None:
    telegram_bot = SimpleNamespace(get_me=AsyncMock(return_value=SimpleNamespace(username="live_username")))
    assert asyncio.run(resolve_identity(telegram_bot)) == "live_username"
    telegram_bot.get_me.assert_awaited_once()


def test_user_isolation_idempotency_and_language(tmp_path) -> None:
    async def exercise() -> None:
        engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'records.db'}")
        maker = async_sessionmaker(engine, expire_on_commit=False)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with maker() as session:
            alpha = await save_bot(session, "Alpha", "alpha_live")
            beta = await save_bot(session, "Beta", "beta_live")
            alpha_user = await get_or_create_user(session, alpha.id, 12345, "Ada")
            same_user = await get_or_create_user(session, alpha.id, 12345, "Ada")
            beta_user = await get_or_create_user(session, beta.id, 12345, "Ada")
            assert alpha_user.id == same_user.id
            assert alpha_user.id != beta_user.id
            await set_language(session, alpha_user, "ar")
            await record_activity(session, alpha.id, alpha_user.id, "language_updated", "User changed language")
            assert await session.scalar(select(func.count()).select_from(BotUser)) == 2
        async with maker() as session:
            users = (await session.scalars(select(BotUser).order_by(BotUser.bot_id))).all()
            assert [(user.bot_id, user.language_code) for user in users] == [(alpha.id, "ar"), (beta.id, "en")]
            assert await session.scalar(select(func.count()).select_from(Activity)) == 1
        await engine.dispose()

    asyncio.run(exercise())


def test_admin_authorization_and_response_schemas(tmp_path) -> None:
    async def seed() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with maker() as session:
            bot = await save_bot(session, "Alpha", "alpha_live")
            user = await get_or_create_user(session, bot.id, 12345, "Ada")
            await record_activity(session, bot.id, user.id, "start", "User started the bot")

    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'admin.db'}")
    maker = async_sessionmaker(engine, expire_on_commit=False)
    asyncio.run(seed())

    async def test_session():
        async with maker() as session:
            yield session

    app.dependency_overrides[get_session] = test_session
    app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None, database_url="sqlite+aiosqlite://", admin_api_key="test-only-key"
    )
    try:
        client = TestClient(app)
        paths = ("overview", "bots", "users", "activities")
        for path in paths:
            assert client.get(f"/api/admin/{path}").status_code == 401
            assert client.get(f"/api/admin/{path}", headers={"X-Admin-Key": "wrong"}).status_code == 401
        headers = {"X-Admin-Key": "test-only-key"}
        assert client.get("/api/admin/overview", headers=headers).json() == {
            "total_bots": 1, "active_bots": 1, "total_users": 1, "total_activities": 1
        }
        bots = client.get("/api/admin/bots", headers=headers).json()
        assert bots == [{"id": 1, "name": "Alpha", "username": "alpha_live", "is_active": True, "registered_user_count": 1}]
        users = client.get("/api/admin/users", headers=headers).json()
        assert set(users[0]) == {"id", "bot_name", "bot_username", "display_name", "language_code", "created_at"}
        activities = client.get("/api/admin/activities", headers=headers).json()
        assert set(activities[0]) == {"event_type", "bot_name", "bot_username", "created_at", "description"}
        assert client.get("/api/admin/users?limit=101", headers=headers).status_code == 422
        assert client.get("/api/admin/activities?limit=101", headers=headers).status_code == 422
        app.dependency_overrides[get_settings] = lambda: Settings(
            _env_file=None, database_url="sqlite+aiosqlite://", admin_api_key=None
        )
        assert client.get("/api/admin/overview", headers=headers).status_code == 401
    finally:
        app.dependency_overrides.clear()
        asyncio.run(engine.dispose())
