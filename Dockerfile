# Använd en mer stabil base image för Playwright
FROM python:3.11-bullseye

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

# Kopiera requirements först för bättre Docker layer caching
COPY requirements.txt .

# Installera Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Installera Playwright browsers (utan --with-deps för att undvika konflikter)
RUN playwright install chromium

# Kopiera alla appfiler
COPY . .

# Skapa data directory för persistent storage
RUN mkdir -p /app/data

# Miljövariabler
ENV PYTHONPATH=/app
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV DATABASE_PATH=/app/data/goldenstat.db

# Exponera port
EXPOSE $PORT

# Starta appen
CMD ["python", "app.py"]