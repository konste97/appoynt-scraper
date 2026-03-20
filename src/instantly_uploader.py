from __future__ import annotations

"""
Instantly.ai Lead Upload — laedt Leads mit E-Mail per API in Instantly-Kampagnen.

- Routet Leads nach category_key in die richtige Kampagne
- Filtert automatisch auf Leads mit E-Mail (Instantly ist eine Cold-Email-Plattform)
- Batching: max. 500 Leads pro API-Call (Instantly-Limit)
- Nutzt retry_request() fuer automatisches Retry mit Backoff
- Graceful Degradation: Wenn nicht konfiguriert, wird der Upload uebersprungen
"""

import logging
from collections import defaultdict

from config.settings import INSTANTLY_API_KEY, INSTANTLY_CAMPAIGNS
from src.utils import retry_request

INSTANTLY_API_URL = "https://api.instantly.ai/api/v2/lead/bulkaddleads"
BATCH_SIZE = 500


def _map_lead_to_instantly(lead: dict) -> dict:
    """Mapped einen Scraper-Lead auf das Instantly-API-Format."""
    return {
        "email": lead["email"],
        "company_name": lead.get("business_name", ""),
        "phone_number": lead.get("phone", ""),
        "website": lead.get("website", ""),
        "custom_variables": {
            "category": lead.get("category_label", ""),
            "street_address": lead.get("street_address", ""),
            "postal_code": lead.get("postal_code", ""),
            "city": lead.get("city", ""),
            "state": lead.get("state", ""),
            "google_rating": str(lead.get("google_rating", "")),
            "google_reviews": str(lead.get("google_reviews", "")),
            "has_whatsapp": str(lead.get("has_whatsapp", False)).lower(),
            "whatsapp_number": lead.get("whatsapp_number", ""),
            "booking_system": lead.get("booking_system", ""),
            "booking_url": lead.get("booking_url", ""),
            "sales_opener": lead.get("sales_opener", ""),
        },
    }


def upload_leads_to_instantly(
    leads: list[dict],
    logger: logging.Logger | None = None,
) -> dict:
    """
    Laedt Leads mit E-Mail-Adresse in die passenden Instantly.ai-Kampagnen hoch.

    Leads werden nach category_key gruppiert und in die jeweils zugeordnete
    Kampagne hochgeladen. Kategorien ohne Kampagne werden uebersprungen.

    Args:
        leads: Alle gesammelten Leads (werden intern auf E-Mail gefiltert)
        logger: Optional - Logger fuer Statusmeldungen

    Returns:
        Dict mit Upload-Statistik: {"uploaded": X, "failed": Y, "skipped": Z, "total_with_email": N}
    """
    log = logger or logging.getLogger(__name__)

    # Konfiguration pruefen
    if not INSTANTLY_API_KEY or not INSTANTLY_CAMPAIGNS:
        log.info(
            "Instantly nicht konfiguriert (INSTANTLY_API_KEY / INSTANTLY_CAMPAIGNS fehlt) "
            "— ueberspringe Upload"
        )
        return {"uploaded": 0, "failed": 0, "skipped": 0, "total_with_email": 0}

    # Nur Leads mit E-Mail filtern
    leads_with_email = [l for l in leads if l.get("email")]
    total = len(leads_with_email)

    if total == 0:
        log.info("Keine Leads mit E-Mail vorhanden — nichts zu uploaden")
        return {"uploaded": 0, "failed": 0, "skipped": 0, "total_with_email": 0}

    # Leads nach category_key gruppieren
    by_category = defaultdict(list)
    for lead in leads_with_email:
        by_category[lead.get("category_key", "unknown")].append(lead)

    log.info(
        f"Instantly Upload: {total} Leads mit E-Mail in {len(by_category)} Kategorien"
    )

    headers = {
        "Authorization": f"Bearer {INSTANTLY_API_KEY}",
        "Content-Type": "application/json",
    }

    uploaded = 0
    failed = 0
    skipped = 0

    for category_key, category_leads in by_category.items():
        campaign_id = INSTANTLY_CAMPAIGNS.get(category_key)

        if not campaign_id:
            skipped += len(category_leads)
            log.info(
                f"  {category_key}: {len(category_leads)} Leads uebersprungen "
                f"(keine Kampagne konfiguriert)"
            )
            continue

        log.info(f"  {category_key}: {len(category_leads)} Leads → Kampagne {campaign_id[:8]}...")

        # Batching (max 500 pro API-Call)
        for i in range(0, len(category_leads), BATCH_SIZE):
            batch = category_leads[i : i + BATCH_SIZE]
            mapped_leads = [_map_lead_to_instantly(lead) for lead in batch]

            payload = {
                "campaign_id": campaign_id,
                "leads": mapped_leads,
            }

            response = retry_request(
                url=INSTANTLY_API_URL,
                method="POST",
                json_body=payload,
                headers=headers,
                logger=log,
            )

            if response is not None and response.status_code < 300:
                uploaded += len(batch)
            else:
                failed += len(batch)
                status = response.status_code if response else "keine Antwort"
                log.error(
                    f"    Upload fehlgeschlagen fuer {category_key} (Status: {status})"
                )

    log.info(
        f"Instantly Upload fertig: {uploaded} hochgeladen, {failed} fehlgeschlagen, "
        f"{skipped} uebersprungen (keine Kampagne)"
    )
    return {"uploaded": uploaded, "failed": failed, "skipped": skipped, "total_with_email": total}
