# Foundation architecture

One FastAPI process serves the API. A separate worker polls two Telegram bots concurrently, with one dispatcher and shared handler factory per bot. PostgreSQL stores bots, users scoped to bots, and activity records. SQLAlchemy provides async sessions; Alembic alone creates and changes tables. The current `/health` route is public and does not check database connectivity. All `/api/admin` routes use `require_admin_key`. This shared key is suitable for a local proof of concept only.

The worker resolves usernames with `getMe`, stores bot identities, and retries each bot separately. Registration is idempotent within a bot, so the same Telegram user can use both bots. Activity descriptions are fixed application strings and never contain message text. The admin API returns bounded lists and no credentials.

The React dashboard is a static Vite build served by nginx on localhost port 5173. Nginx proxies `/api` to FastAPI on the Compose network, so no wildcard CORS policy is needed. The operator enters the shared admin key manually; React holds it in memory and sends it in `X-Admin-Key` on each read request. Reload and Disconnect clear it. This protects a local demonstration but does not provide user accounts, sessions, or production authentication. The dashboard has no write controls. No webhooks, scheduled jobs, or public deployment are configured.
