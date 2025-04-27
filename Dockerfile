FROM python:3.13-alpine

WORKDIR /app

# Get UV
COPY --from=ghcr.io/astral-sh/uv:0.6.17 /uv /uvx /bin/
ENV PATH="/app/.venv/bin:$PATH"

# Copy files
COPY pyproject.toml uv.lock ./
COPY mcpbot ./mcpbot

# Install dependencies
RUN uv sync --locked --no-install-project

EXPOSE 8000

ENTRYPOINT ["uvicorn", "mcpbot.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
