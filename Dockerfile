FROM python:3.14-slim-bookworm@sha256:23c59390fc717bf09f9336908199a0ae75d9c4264bf296123f94ad772fea3b52

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    APP_ENV=production \
    CORPUS_PATH=/corpus \
    DB_PATH=/app/corpus.db \
    OFFLINE_PACKS_DIR=/app/offline-packs

WORKDIR /app

COPY web/requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt \
    && groupadd --gid 10001 app \
    && useradd --uid 10001 --gid 10001 --home-dir /app --shell /usr/sbin/nologin app \
    && mkdir -p /app/offline-packs /corpus \
    && chown -R 10001:10001 /app /corpus

COPY --chown=10001:10001 web/app/ ./app/
COPY --chown=10001:10001 web/templates/ ./templates/
COPY --chown=10001:10001 web/static/ ./static/

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD ["python", "-c", "import json,urllib.request; data=json.load(urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4)); raise SystemExit(0 if data.get('corpus_db', {}).get('ok') is True else 1)"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
