# Använd en mer stabil base image för Playwright
FROM python:3.11-bullseye

# Build args för git clone med LFS
ARG RAILWAY_GIT_COMMIT_SHA
ARG RAILWAY_GIT_BRANCH=main

WORKDIR /app

# Installera systempaket och dependencies för Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
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

# Installera Playwright browsers (utan --with-deps för att undvika konflikter)
RUN playwright install chromium

# Miljövariabler
ENV PYTHONPATH=/app
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Exponera port
EXPOSE $PORT

# Starta appen
CMD ["python", "app.py"]