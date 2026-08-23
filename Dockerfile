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
COPY deploy/snowflake-config.toml /root/.snowflake/config.toml
RUN chmod 600 /root/.snowflake/config.toml

EXPOSE 8080

CMD ["sh", "-c", ".venv/bin/streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT:-8080} --server.headless=true --browser.gatherUsageStats=false"]
