import json
import logging
import re
from datetime import datetime, timezone

from app.config import get_settings


TOKEN_PATTERN = re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{20,}\b")


class JsonFormatter(logging.Formatter):
    def __init__(self) -> None:
        super().__init__()
        settings = get_settings()
        self.secrets = tuple(
            value for value in (
                settings.telegram_bot_alpha_token,
                settings.telegram_bot_beta_token,
                settings.admin_api_key,
                settings.database_url,
            ) if value
        )

    def redact(self, value: str) -> str:
        for secret in self.secrets:
            value = value.replace(secret, "[REDACTED]")
        return TOKEN_PATTERN.sub("[REDACTED]", value)

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": self.redact(record.getMessage()),
        }
        if record.exc_info:
            payload["exception"] = self.redact(self.formatException(record.exc_info))
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
