FROM python:3.10-slim-bookworm

WORKDIR /usr/src/app

# 🔧 Install system deps (IMPORTANT: pg_dump)
RUN apt-get update && apt-get install -y \
    git \
    postgresql-client \
    gzip \
    && rm -rf /var/lib/apt/lists/*

# 📦 Copy requirements first (better caching)
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 📁 Copy project
COPY . .

# 🚀 Run both Flask + Bot
CMD sh -c "rm -rf .git && gunicorn app:app --bind 0.0.0.0:5000 & python3 bot.py"
