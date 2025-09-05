FROM python:3.11-slim

# Қажетті build құралдары
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# requirements.txt көшіру және орнату
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Қалған кодты көшіру
COPY ./app ./app

# Default порт
ENV PORT=8080
EXPOSE 8080

# Gunicorn арқылы қосу
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "2", "-b", "0.0.0.0:8080", "app.main:app"]
