FROM python:3.13-alpine AS base

RUN apk add --no-cache curl

WORKDIR /app

FROM base AS builder

RUN curl -LsSf https://astral.sh/uv/install.sh | UV_NO_MODIFY_PATH=1 sh

ENV PATH="/root/.local/bin:${PATH}"

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

FROM base AS final

COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:9000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "run:app"]