FROM python:3.12-slim

WORKDIR /app

# No apt-get: wheels cover our deps; avoids Debian mirror timeouts on some networks.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts

RUN mkdir -p /app/data

ENV PYTHONUNBUFFERED=1
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV UVICORN_WORKERS=2

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; r=httpx.get('http://127.0.0.1:8000/health', timeout=3); exit(0 if r.status_code==200 else 1)"

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS}"]
