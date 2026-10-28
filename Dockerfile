FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY nakshatra ./nakshatra

# Ensure runtime data directories exist without requiring uncommitted git assets
RUN mkdir -p corpus index

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir . google-genai

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

ENV PORT=8004
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

EXPOSE 8004

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

CMD ["uvicorn", "nakshatra.api:app", "--host", "0.0.0.0", "--port", "8004"]
