import json
from functools import lru_cache
from importlib.resources import files

SUPPORTED_LANGUAGES = {"en", "ar"}


@lru_cache(maxsize=2)
def messages(language: str) -> dict[str, str]:
    code = language if language in SUPPORTED_LANGUAGES else "en"
    return json.loads(files("app.i18n").joinpath(f"{code}.json").read_text(encoding="utf-8"))


def translate(language: str, key: str, **values: str) -> str:
    return messages(language)[key].format(**values)
