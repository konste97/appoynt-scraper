FROM python:3.12-slim

WORKDIR /app

# Cron installieren
RUN apt-get update && apt-get install -y --no-install-recommends cron && rm -rf /var/lib/apt/lists/*

# Dependencies installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code reinkopieren
COPY . .

# Output-Ordner anlegen
RUN mkdir -p output/checkpoints logs

# Crontab einrichten (woechentlicher Auto-Run)
COPY crontab /etc/cron.d/scraper-cron
RUN chmod 0644 /etc/cron.d/scraper-cron && crontab /etc/cron.d/scraper-cron

# Wrapper-Script ausfuehrbar machen + Cron im Vordergrund starten
RUN chmod +x /app/scripts/run-scraper.sh
CMD cron -f
