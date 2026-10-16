from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.security import require_admin_key
from app.db import get_session
from app.models import Activity, Bot, BotUser

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin_key)])
Session = Annotated[AsyncSession, Depends(get_session)]


class Overview(BaseModel):
    total_bots: int
    active_bots: int
    total_users: int
    total_activities: int


class BotSummary(BaseModel):
    id: int
    name: str
    username: str
    is_active: bool
    registered_user_count: int


class UserSummary(BaseModel):
    id: int
    bot_name: str
    bot_username: str
    display_name: str
    language_code: str
    created_at: datetime


class ActivitySummary(BaseModel):
    event_type: str
    bot_name: str
    bot_username: str
    created_at: datetime
    description: str


@router.get("/overview", response_model=Overview)
async def overview(session: Session) -> Overview:
    return Overview(
        total_bots=await session.scalar(select(func.count()).select_from(Bot)) or 0,
        active_bots=await session.scalar(select(func.count()).select_from(Bot).where(Bot.is_active.is_(True))) or 0,
        total_users=await session.scalar(select(func.count()).select_from(BotUser)) or 0,
        total_activities=await session.scalar(select(func.count()).select_from(Activity)) or 0,
    )


@router.get("/bots", response_model=list[BotSummary])
async def bots(session: Session) -> list[BotSummary]:
    rows = await session.execute(
        select(Bot.id, Bot.name, Bot.username, Bot.is_active, func.count(BotUser.id).label("registered_user_count"))
        .outerjoin(BotUser, BotUser.bot_id == Bot.id)
        .group_by(Bot.id)
        .order_by(Bot.id)
    )
    return [BotSummary(**row._mapping) for row in rows]


@router.get("/users", response_model=list[UserSummary])
async def users(session: Session, limit: Annotated[int, Query(ge=1, le=100)] = 50) -> list[UserSummary]:
    rows = await session.execute(
        select(
            BotUser.id, Bot.name.label("bot_name"), Bot.username.label("bot_username"),
            BotUser.display_name, BotUser.language_code, BotUser.created_at,
        )
        .join(Bot, Bot.id == BotUser.bot_id)
        .order_by(BotUser.created_at.desc(), BotUser.id.desc())
        .limit(limit)
    )
    return [UserSummary(**row._mapping) for row in rows]


@router.get("/activities", response_model=list[ActivitySummary])
async def activities(session: Session, limit: Annotated[int, Query(ge=1, le=100)] = 50) -> list[ActivitySummary]:
    rows = await session.execute(
        select(
            Activity.event_type, Bot.name.label("bot_name"), Bot.username.label("bot_username"),
            Activity.created_at, Activity.description,
        )
        .join(Bot, Bot.id == Activity.bot_id)
        .order_by(Activity.created_at.desc(), Activity.id.desc())
        .limit(limit)
    )
    return [ActivitySummary(**row._mapping) for row in rows]
