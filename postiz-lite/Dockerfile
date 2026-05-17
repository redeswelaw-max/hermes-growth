FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

ENV DB_PATH=/data/postiz_lite.db
ENV API_KEY=postiz-lite-demo-key-change-me
ENV PORT=5000

RUN mkdir -p /data

CMD ["python", "main.py"]
