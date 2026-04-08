"""
Einmaliger Retry-Upload fuer Leads die wegen des Instantly-Monatslimits nicht hochgeladen wurden.

Liest leads_with_email.csv und laedt die noch fehlenden Leads ins Instantly-Limit hoch.

Ausfuehren im Container:
    python scripts/retry_instantly_upload.py
"""

import csv
import logging
import sys
from pathlib import Path

# Projektroot zum Python-Path hinzufuegen
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import LEADS_WITH_EMAIL_CSV
from src.instantly_uploader import upload_leads_to_instantly

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s | %(message)s",
)
log = logging.getLogger(__name__)


def load_leads_from_csv(csv_path: Path) -> list[dict]:
    if not csv_path.exists():
        log.error(f"CSV nicht gefunden: {csv_path}")
        return []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main() -> None:
    log.info(f"Lade Leads aus {LEADS_WITH_EMAIL_CSV}")
    leads = load_leads_from_csv(LEADS_WITH_EMAIL_CSV)

    if not leads:
        log.warning("Keine Leads gefunden — nichts zu tun.")
        return

    log.info(f"{len(leads)} Leads in CSV gefunden")

    # CSV-Spalten auf interne Feldnamen normalisieren (CSV hat HubSpot-Header wie "Email", "Company name")
    COLUMN_MAP = {
        "Company name": "business_name",
        "Industry": "category_label",
        "Street address": "street_address",
        "Zip": "postal_code",
        "City": "city",
        "State/Region": "state",
        "Phone number": "phone",
        "Website URL": "website",
        "Email": "email",
        "google_rating": "google_rating",
        "google_reviews": "google_reviews",
        "branche": "category_key",
        "has_whatsapp": "has_whatsapp",
        "whatsapp_number": "whatsapp_number",
        "booking_system": "booking_system",
        "booking_url": "booking_url",
        "sales_opener": "sales_opener",
    }
    normalized = []
    for row in leads:
        lead = {COLUMN_MAP.get(k, k): v for k, v in row.items()}
        normalized.append(lead)

    # Nur WA-Leads hochladen
    wa_leads = [l for l in normalized if l.get("has_whatsapp", "").lower() == "true"]
    skipped_no_wa = len(normalized) - len(wa_leads)
    if skipped_no_wa:
        log.info(f"{skipped_no_wa} Leads ohne WhatsApp uebersprungen")
    log.info(f"{len(wa_leads)} Leads mit WhatsApp werden hochgeladen")

    result = upload_leads_to_instantly(wa_leads, logger=log)

    log.info(
        f"Ergebnis: {result['uploaded']} hochgeladen, "
        f"{result['failed']} fehlgeschlagen, "
        f"{result['skipped']} uebersprungen"
    )


if __name__ == "__main__":
    main()
