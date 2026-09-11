FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev
COPY seed ./seed
COPY semantic ./semantic
COPY data ./data
COPY docs ./docs
ENV PORT=8080
CMD ["uv", "run", "--no-sync", "ai-tracker", "serve"]
