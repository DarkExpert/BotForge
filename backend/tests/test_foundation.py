import json
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.security import require_admin_key
from app.config import Settings, get_settings
from app.main import app


def test_health_is_public() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_translations_are_valid_and_matching() -> None:
    directory = Path(__file__).resolve().parents[1] / "app" / "i18n"
    english = json.loads((directory / "en.json").read_text(encoding="utf-8"))
    arabic = json.loads((directory / "ar.json").read_text(encoding="utf-8"))
    required = {"welcome", "language_selection", "language_updated", "generic_error", "help", "unsupported"}
    assert set(english) == set(arabic) == required
    assert all(isinstance(value, str) and value for value in (*english.values(), *arabic.values()))


def test_tokens_are_optional(monkeypatch) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_ALPHA_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_BOT_BETA_TOKEN", raising=False)
    settings = Settings(_env_file=None, database_url="postgresql+asyncpg://example:example@localhost/test")
    assert settings.telegram_bot_alpha_token is None
    assert settings.telegram_bot_beta_token is None


def test_admin_key_missing_invalid_valid() -> None:
    protected = FastAPI()

    @protected.get("/admin", dependencies=[Depends(require_admin_key)])
    def admin() -> dict[str, bool]:
        return {"ok": True}

    protected.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None, database_url="postgresql+asyncpg://example:example@localhost/test", admin_api_key="test-only-key"
    )
    client = TestClient(protected)
    assert client.get("/admin").status_code == 401
    assert client.get("/admin", headers={"X-Admin-Key": "wrong"}).status_code == 401
    assert client.get("/admin", headers={"X-Admin-Key": "test-only-key"}).status_code == 200
    protected.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None, database_url="postgresql+asyncpg://example:example@localhost/test", admin_api_key=None
    )
    assert client.get("/admin", headers={"X-Admin-Key": "test-only-key"}).status_code == 401
