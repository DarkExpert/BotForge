# BotForge v0.1.0 — Initial public proof of concept

BotForge is a local Telegram multi-bot management demo. Two aiogram bots share command handlers while keeping bot identities, registered users, language preferences, and activity records separate in PostgreSQL. A FastAPI admin API and a responsive React dashboard provide a read-only view of the system.

## Included

- Two concurrent Telegram long-polling bots in a dedicated worker process
- `/start`, `/language`, and `/help` with English and Arabic translations
- Async SQLAlchemy models and an Alembic migration for bots, users, and activities
- Read-only API-key-protected overview, bots, users, and activities endpoints
- React dashboard with in-memory admin key entry, refresh, and responsive layouts
- Docker Compose services for PostgreSQL, backend, bot worker, and dashboard
- Automated backend tests and TypeScript/build checks

## Known limitations

This is a localhost-only proof of concept. The admin API uses one shared key rather than user accounts or role-based authorization. Bot tokens and the key are configured manually in `.env`; the dashboard never stores the key. The users and activities API returns the newest 50 records by default, with a maximum of 100 and no pagination. There is no public deployment, webhook mode, or production operations setup.

## Getting started

Follow the [README](../README.md) for environment setup, migrations, Docker commands, dashboard access, and manual Telegram checks.
