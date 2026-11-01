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

# Ladda ner databaser från GitHub Release. En nedladdning som avbryts kan
# lämna en halv fil utan att curl klagar, så varje databas kontrolleras och
# hämtas om. Går det ändå inte stoppas bygget och den förra deployen ligger kvar.
RUN for db in goldenstat cups riksserien sommarserien; do \
        for attempt in 1 2 3; do \
            curl -fsSL --retry 3 -o /app/$db.db \
                "https://github.com/mikaaal/goldenstat/releases/download/db-latest/$db.db" \
                && python /app/check_database.py /app/$db.db && break; \
            if [ $attempt = 3 ]; then echo "$db.db kunde inte hämtas hel" >&2; exit 1; fi; \
            sleep 10; \
        done; \
    done \
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