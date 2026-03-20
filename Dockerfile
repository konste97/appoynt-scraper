FROM python:3.12-slim

WORKDIR /app

# Dependencies installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code reinkopieren
COPY . .

# Output-Ordner anlegen
RUN mkdir -p output/checkpoints logs

# Container bleibt am Leben (kein Webserver, kein Port)
CMD ["tail", "-f", "/dev/null"]
