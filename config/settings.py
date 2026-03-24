"""
Zentrale Konfiguration fuer den APPOYNT Lead Scraper.

Liest den Google API Key aus der .env-Datei und definiert
alle wichtigen Parameter wie Rate Limits, Timeouts usw.
"""

import json as _json
import os
from pathlib import Path
from dotenv import load_dotenv

# Projektverzeichnis bestimmen (ein Ordner ueber /config)
BASE_DIR = Path(__file__).resolve().parent.parent

# .env-Datei laden (dort liegt dein API Key)
load_dotenv(BASE_DIR / ".env")

# --- Google Places API ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# --- Instantly.ai ---
INSTANTLY_API_KEY = os.getenv("INSTANTLY_API_KEY", "")
# Mapping: category_key -> Instantly Campaign ID (als JSON-String in Env-Var)
# z.B. INSTANTLY_CAMPAIGNS={"friseur":"abc-123","yoga":"def-456",...}
INSTANTLY_CAMPAIGNS = _json.loads(os.getenv("INSTANTLY_CAMPAIGNS", "{}"))

# Radius in Metern fuer die Places-Suche rund um das Stadtzentrum.
# 30km deckt auch groessere Staedte gut ab.
SEARCH_RADIUS_METERS = 30000

# --- Lead-Limit pro Durchlauf ---
# Nach dieser Anzahl neuer Leads stoppt der Scraper.
# Naechster Run macht per Checkpoint dort weiter.
MAX_LEADS_PER_RUN = int(os.getenv("MAX_LEADS_PER_RUN", "500"))

# --- Max Leads pro Stadt/Kategorie-Kombi ---
# Verhindert dass eine einzelne Kategorie das gesamte Limit aufbraucht.
MAX_LEADS_PER_COMBO = int(os.getenv("MAX_LEADS_PER_COMBO", "35"))

# --- Rate Limiting ---
# Sekunden zwischen zwei Requests (1.0 = max 1 Request/Sek.)
REQUEST_DELAY_SECONDS = 1.0

# --- Retry-Logik ---
MAX_RETRIES = 3
# Wartezeit in Sekunden, die sich pro Retry verdoppelt (Exponential Backoff)
RETRY_BACKOFF_SECONDS = 2.0

# --- Timeouts ---
# Max. Wartezeit in Sekunden fuer einen einzelnen HTTP-Request
HTTP_TIMEOUT_SECONDS = 15

# --- Pfade ---
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"
CHECKPOINT_DIR = BASE_DIR / "output" / "checkpoints"

CITIES_FILE = BASE_DIR / "config" / "cities.json"
CATEGORIES_FILE = BASE_DIR / "config" / "categories.json"

# --- Output-Dateien ---
LEADS_WITH_EMAIL_CSV = OUTPUT_DIR / "leads_with_email.csv"
LEADS_COLD_CALLING_CSV = OUTPUT_DIR / "leads_cold_calling.csv"
LEADS_WHATSAPP_READY_CSV = OUTPUT_DIR / "leads_whatsapp_ready.csv"
