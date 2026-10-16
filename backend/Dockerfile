FROM python:3.12-slim AS base
WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic
RUN python -m pip install --no-cache-dir --upgrade "pip>=26.2,<27" \
    && python -m pip install --no-cache-dir .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS test
COPY tests ./tests
RUN python -m pip install --no-cache-dir ".[dev]"
CMD ["pytest", "-q"]

FROM base AS production
