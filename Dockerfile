FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    HOME=/root

WORKDIR /app

RUN pip install --no-cache-dir uv==0.8.4

COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
COPY data ./data
RUN uv sync --frozen --no-dev

COPY app.py ./
COPY deploy/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh
COPY deploy/snowflake-config.toml /root/.snowflake/config.toml
RUN chmod 600 /root/.snowflake/config.toml

EXPOSE 8080

# Default remains the public Streamlit app; BIDPILOT_MODE=api serves the agent surface.
CMD ["./entrypoint.sh"]
