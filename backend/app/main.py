from fastapi import FastAPI

from app.api.admin import router as admin_router
from app.logging_config import configure_logging

configure_logging()
app = FastAPI(title="BotForge", version="0.1.0")
app.include_router(admin_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}
