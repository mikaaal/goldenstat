# Python base image
FROM python:3.11-slim

# Build args för git clone
ARG RAILWAY_GIT_COMMIT_SHA
ARG RAILWAY_GIT_BRANCH=main

WORKDIR /app

# Installera systempaket
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# Cache-bust: detta ändras vid varje commit så Docker hämtar nya filer
ARG CACHEBUST=${RAILWAY_GIT_COMMIT_SHA:-1}

# Klona repot (utan LFS)
RUN git clone --branch ${RAILWAY_GIT_BRANCH:-main} --single-branch --depth 1 \
    https://github.com/mikaaal/goldenstat.git /tmp/repo \
    && cp -r /tmp/repo/* /app/ \
    && rm -rf /tmp/repo

# Ladda ner databaser från GitHub Release
RUN curl -sL -o /app/goldenstat.db "https://github.com/mikaaal/goldenstat/releases/download/db-latest/goldenstat.db" \
    && curl -sL -o /app/cups.db "https://github.com/mikaaal/goldenstat/releases/download/db-latest/cups.db" \
    && curl -sL -o /app/riksserien.db "https://github.com/mikaaal/goldenstat/releases/download/db-latest/riksserien.db" \
    && echo "Databases downloaded:" && ls -lh /app/*.db

# Installera Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Miljövariabler
ENV PYTHONPATH=/app
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Exponera port
EXPOSE $PORT

# Starta appen
CMD ["python", "app.py"]