from __future__ import annotations

"""
Buchungssystem-Erkennung auf Business-Websites.

Erkennt bekannte Systeme anhand von URLs, Script-Tags und Widgets:
- Calendly, Acuity Scheduling, SimplyBook.me
- Booksy, Treatwell, Shore, Planity
- Google Calendar, Microsoft Bookings
- Timify, Terminland, Doctolib

Fallback: Generische "Termin buchen" Buttons/Links (deutsch)
"""

import re
from bs4 import BeautifulSoup


# Bekannte Buchungssysteme mit URL- und HTML-Erkennungsmustern.
# Reihenfolge = Prioritaet (haeufigste zuerst fuer schnellere Erkennung)
BOOKING_SYSTEMS = [
    {
        "name": "Treatwell",
        "url_patterns": [r"treatwell\.(de|com|co\.uk)/[a-zA-Z0-9_\-/]+"],
        "html_patterns": [r"treatwell\.(de|com)", r"mytreatwell\.(de|com)"],
    },
    {
        "name": "Booksy",
        "url_patterns": [r"booksy\.com/[a-z]{2}-[a-z]{2}/[a-zA-Z0-9_\-/]+"],
        "html_patterns": [r"booksy\.com", r"booksy-widget"],
    },
    {
        "name": "Shore",
        "url_patterns": [r"shore\.com/[a-zA-Z0-9_\-/]+"],
        "html_patterns": [r"shore\.com", r"shore-booking", r"shore-widget"],
    },
    {
        "name": "Planity",
        "url_patterns": [r"planity\.(com|de)/[a-zA-Z0-9_\-/]+"],
        "html_patterns": [r"planity\.(com|de)"],
    },
    {
        "name": "Calendly",
        "url_patterns": [r"calendly\.com/[a-zA-Z0-9_\-/]+"],
        "html_patterns": [r"calendly-inline-widget", r"calendly-badge-widget", r"assets\.calendly\.com"],
    },
    {
        "name": "Acuity Scheduling",
        "url_patterns": [r"app\.acuityscheduling\.com/[a-zA-Z0-9_\-/]+"],
        "html_patterns": [r"acuityscheduling\.com", r"acuity-embed"],
    },
    {
        "name": "SimplyBook.me",
        "url_patterns": [r"[a-zA-Z0-9\-]+\.simplybook\.me"],
        "html_patterns": [r"simplybook\.me", r"simplybookwidget"],
    },
    {
        "name": "Timify",
        "url_patterns": [r"timify\.com/[a-zA-Z0-9_\-/]+"],
        "html_patterns": [r"timify\.com"],
    },
    {
        "name": "Terminland",
        "url_patterns": [r"terminland\.(de|com)/[a-zA-Z0-9_\-/]+"],
        "html_patterns": [r"terminland\.(de|com)"],
    },
    {
        "name": "Doctolib",
        "url_patterns": [r"doctolib\.de/[a-zA-Z0-9_\-/]+"],
        "html_patterns": [r"doctolib\.de"],
    },
    {
        "name": "Google Calendar",
        "url_patterns": [r"calendar\.google\.com/calendar/appointments"],
        "html_patterns": [r"calendar\.google\.com"],
    },
    {
        "name": "Microsoft Bookings",
        "url_patterns": [
            r"outlook\.office365\.com/owa/calendar",
            r"outlook\.office\.com/bookwithme",
        ],
        "html_patterns": [r"outlook\.office365\.com", r"bookwithme"],
    },
]

# Deutsche Keywords fuer generische "Termin buchen" Buttons/Links
BOOKING_KEYWORDS_DE = [
    r"online\s*termin\s*buchen",
    r"termin\s*online\s*buchen",
    r"jetzt\s*termin\s*buchen",
    r"termin\s*vereinbaren",
    r"termin\s*reservieren",
    r"online\s*buchung",
    r"termin\s*buchen",
    r"termine\s*buchen",
    r"book\s*now",
    r"book\s*appointment",
    r"online\s*booking",
]


def detect_booking_system(html: str) -> dict:
    """
    Erkennt Buchungs-/Terminbuchungssysteme im HTML einer Website.

    Zwei Erkennungs-Strategien:
    1. Bekannte Systeme anhand von URLs und Widgets (Calendly, Treatwell, etc.)
    2. Generische "Termin buchen" Buttons als Fallback

    Args:
        html: Der HTML-Quelltext der Seite

    Returns:
        Dict mit:
            has_booking (bool): Buchungssystem erkannt?
            system_name (str): Name des Systems (z.B. "Calendly")
            booking_url (str): URL zur Buchungsseite
            generic_booking (bool): Nur generischer Button gefunden?
            evidence (list[str]): Was wurde gefunden
    """
    result = {
        "has_booking": False,
        "system_name": "",
        "booking_url": "",
        "generic_booking": False,
        "evidence": [],
    }

    # Strategie 1: Bekannte Buchungssysteme erkennen
    for system in BOOKING_SYSTEMS:
        found = False

        # URL-Muster in hrefs und rohem HTML suchen
        for pattern in system["url_patterns"]:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                found = True
                result["has_booking"] = True
                result["system_name"] = system["name"]
                result["booking_url"] = match.group(0)
                result["evidence"].append(f"{system['name']} URL gefunden")
                break

        if found:
            break

        # HTML-Muster (Scripts, Iframes, Widget-Divs)
        for pattern in system["html_patterns"]:
            if re.search(pattern, html, re.IGNORECASE):
                found = True
                result["has_booking"] = True
                result["system_name"] = system["name"]
                result["evidence"].append(f"{system['name']} Widget/Script gefunden")
                break

        if found:
            break

    # Strategie 2: Generische Termin-Buttons (nur wenn kein System erkannt)
    if not result["has_booking"]:
        soup = BeautifulSoup(html, "html.parser")

        for el in soup.find_all(["a", "button"]):
            el_text = el.get_text(strip=True).lower()

            for kw_pattern in BOOKING_KEYWORDS_DE:
                if re.search(kw_pattern, el_text, re.IGNORECASE):
                    result["has_booking"] = True
                    result["generic_booking"] = True
                    result["evidence"].append(
                        f"Button/Link: '{el.get_text(strip=True)[:50]}'"
                    )
                    el_href = el.get("href", "")
                    if el_href and el_href.startswith("http"):
                        result["booking_url"] = el_href
                    break

            if result["has_booking"]:
                break

    # Duplikate entfernen
    result["evidence"] = list(set(result["evidence"]))

    return result
