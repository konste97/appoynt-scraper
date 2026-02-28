from __future__ import annotations

"""
Website-Analyse: Besucht Business-Websites und extrahiert alle
Sales-relevanten Signale in einem einzigen Durchlauf.

Signale die extrahiert werden:
- E-Mail-Adressen (wie bisher ueber email_extractor)
- WhatsApp-Praesenz (wa.me Links, Buttons, etc.)
- Buchungssystem (Calendly, Treatwell, etc.)

Der Vorteil: Die Website wird nur EINMAL besucht, und das gleiche HTML
wird an alle Detektoren weitergegeben. Keine zusaetzlichen Requests noetig.
"""

import logging
import time
from urllib.parse import urljoin, urlparse

import requests

from config.settings import HTTP_TIMEOUT_SECONDS, REQUEST_DELAY_SECONDS
from src.email_extractor import _extract_emails_from_html, _pick_best_email
from src.whatsapp_detector import detect_whatsapp
from src.booking_detector import detect_booking_system


# Typische Unterseiten auf denen deutsche Businesses Kontaktinfos zeigen
CONTACT_PATHS = [
    "/kontakt",
    "/contact",
    "/impressum",
    "/about",
    "/ueber-uns",
    "/about-us",
]

USER_AGENT = "Mozilla/5.0 (compatible; AppointBot/1.0)"


def _fetch_page(url: str, logger: logging.Logger | None) -> str | None:
    """
    Laedt eine einzelne Seite und gibt den HTML-Quelltext zurueck.
    Gibt None zurueck bei 404 oder Fehlern.
    """
    try:
        time.sleep(REQUEST_DELAY_SECONDS)
        response = requests.get(
            url,
            timeout=HTTP_TIMEOUT_SECONDS,
            headers={"User-Agent": USER_AGENT},
            allow_redirects=True,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        if logger:
            logger.debug(f"Fehler beim Laden von {url}: {e}")
        return None


def analyze_website(website_url: str, logger: logging.Logger | None = None) -> dict:
    """
    Hauptfunktion: Besucht eine Business-Website und extrahiert alle Signale.

    Ablauf:
    1. Hauptseite laden
    2. Falls keine E-Mail: Unterseiten pruefen (/kontakt, /impressum)
    3. Alle geladenen HTML-Seiten an die Detektoren geben:
       - E-Mail-Extraktion
       - WhatsApp-Erkennung
       - Buchungssystem-Erkennung

    Args:
        website_url: URL der Business-Website
        logger: Logger fuer Statusmeldungen

    Returns:
        Dict mit allen erkannten Signalen:
            email, has_whatsapp, whatsapp_number, has_booking_system,
            booking_system_name, booking_url, has_generic_booking
    """
    result = {
        "email": "",
        "has_whatsapp": False,
        "whatsapp_number": "",
        "whatsapp_evidence": [],
        "has_booking_system": False,
        "booking_system_name": "",
        "booking_url": "",
        "has_generic_booking": False,
        "booking_evidence": [],
    }

    if not website_url:
        return result

    # URL normalisieren
    if not website_url.startswith(("http://", "https://")):
        website_url = "https://" + website_url

    all_emails = []
    all_htmls = []  # Alle geladenen Seiten fuer die Detektoren

    # Schritt 1: Hauptseite laden
    html = _fetch_page(website_url, logger)
    if html is None:
        return result

    all_htmls.append(html)
    emails = _extract_emails_from_html(html)
    all_emails.extend(emails)

    if logger:
        logger.debug(f"Hauptseite {website_url}: {len(emails)} E-Mail(s)")

    # Schritt 2: Falls keine E-Mail, Unterseiten pruefen
    if not all_emails:
        base_url = f"{urlparse(website_url).scheme}://{urlparse(website_url).netloc}"

        for path in CONTACT_PATHS:
            sub_url = urljoin(base_url, path)
            sub_html = _fetch_page(sub_url, logger)
            if sub_html is None:
                continue

            all_htmls.append(sub_html)
            emails = _extract_emails_from_html(sub_html)
            all_emails.extend(emails)

            if logger:
                logger.debug(f"Unterseite {sub_url}: {len(emails)} E-Mail(s)")

            if all_emails:
                break

    # Schritt 3: Beste E-Mail auswaehlen
    best = _pick_best_email(list(set(all_emails)))
    if best:
        result["email"] = best.replace("mailto:", "").replace("%20", "").strip()

    # Schritt 4: WhatsApp-Erkennung auf ALLEN geladenen Seiten
    for html in all_htmls:
        wa = detect_whatsapp(html)
        if wa["has_whatsapp"]:
            result["has_whatsapp"] = True
            if wa["number"] and not result["whatsapp_number"]:
                result["whatsapp_number"] = wa["number"]
            result["whatsapp_evidence"].extend(wa["evidence"])

    result["whatsapp_evidence"] = list(set(result["whatsapp_evidence"]))

    # Schritt 5: Buchungssystem-Erkennung auf ALLEN geladenen Seiten
    for html in all_htmls:
        bk = detect_booking_system(html)
        if bk["has_booking"]:
            result["has_booking_system"] = True
            if bk["system_name"] and not result["booking_system_name"]:
                result["booking_system_name"] = bk["system_name"]
            if bk["booking_url"] and not result["booking_url"]:
                result["booking_url"] = bk["booking_url"]
            if bk["generic_booking"]:
                result["has_generic_booking"] = True
            result["booking_evidence"].extend(bk["evidence"])

    result["booking_evidence"] = list(set(result["booking_evidence"]))

    # Zusammenfassung loggen
    if logger:
        signals = []
        if result["email"]:
            signals.append(f"E-Mail: {result['email']}")
        if result["has_whatsapp"]:
            wa_info = "WhatsApp: ja"
            if result["whatsapp_number"]:
                wa_info += f" (Nr: {result['whatsapp_number']})"
            signals.append(wa_info)
        if result["has_booking_system"]:
            bk_info = f"Buchung: {result['booking_system_name'] or 'generisch'}"
            signals.append(bk_info)
        if signals:
            logger.debug(f"Signale: {' | '.join(signals)}")

    return result
