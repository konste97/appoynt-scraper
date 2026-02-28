from __future__ import annotations

"""
WhatsApp-Erkennung auf Business-Websites.

Sucht nach:
1. wa.me Links (z.B. wa.me/491234567890) -> zuverlaessigste Methode
2. api.whatsapp.com Links
3. WhatsApp-Buttons/Icons (CSS-Klassen, Bilder)
4. "WhatsApp" Text-Erwaehnung im Kontext von Kontakt/Kommunikation
"""

import re
from bs4 import BeautifulSoup


# Regex: wa.me Links mit Telefonnummer
WAME_REGEX = re.compile(
    r"(?:https?://)?(?:www\.)?wa\.me/(\+?\d{7,15})",
    re.IGNORECASE,
)

# Regex: WhatsApp API Links mit Telefonnummer
WHATSAPP_API_REGEX = re.compile(
    r"(?:https?://)?api\.whatsapp\.com/send\?phone=(\d{7,15})",
    re.IGNORECASE,
)

# CSS-Klassen die auf WhatsApp-Widgets hindeuten
WHATSAPP_CLASS_PATTERNS = [
    "whatsapp",
    "wa-button",
    "wa-chat",
    "wa_btn",
    "whatsapp-button",
    "whatsapp-chat",
    "whatsapp-widget",
    "wh-api",
    "wa-widget",
    "whatsapp-float",
]


def detect_whatsapp(html: str) -> dict:
    """
    Erkennt WhatsApp-Praesenz im HTML einer Website.

    Vier Erkennungs-Strategien (von zuverlaessig bis unsicher):
    1. wa.me Links mit Telefonnummer
    2. api.whatsapp.com Links
    3. WhatsApp CSS-Klassen (Buttons, Widgets)
    4. "WhatsApp" Text im Kontaktbereich

    Args:
        html: Der HTML-Quelltext der Seite

    Returns:
        Dict mit:
            has_whatsapp (bool): WhatsApp erkannt?
            number (str): Telefonnummer falls extrahierbar
            evidence (list[str]): Was wurde gefunden
    """
    result = {
        "has_whatsapp": False,
        "number": "",
        "evidence": [],
    }

    # Strategie 1: wa.me Links (zuverlaessigste Methode)
    wame_matches = WAME_REGEX.findall(html)
    if wame_matches:
        result["has_whatsapp"] = True
        result["number"] = wame_matches[0].lstrip("+")
        result["evidence"].append("wa.me Link")

    # Strategie 2: api.whatsapp.com Links
    api_matches = WHATSAPP_API_REGEX.findall(html)
    if api_matches:
        result["has_whatsapp"] = True
        if not result["number"]:
            result["number"] = api_matches[0]
        result["evidence"].append("api.whatsapp.com Link")

    # Strategie 3: WhatsApp CSS-Klassen/IDs im DOM
    soup = BeautifulSoup(html, "html.parser")

    for pattern in WHATSAPP_CLASS_PATTERNS:
        # class-Attribut durchsuchen
        elements = soup.find_all(
            attrs={
                "class": lambda c: (
                    c
                    and pattern
                    in (
                        " ".join(c).lower()
                        if isinstance(c, list)
                        else c.lower()
                    )
                )
            }
        )
        if elements:
            result["has_whatsapp"] = True
            result["evidence"].append(f"CSS-Klasse '{pattern}'")
            break  # Ein Treffer reicht

    # WhatsApp in href-Attributen (ueber wa.me hinaus)
    for link in soup.find_all("a", href=True):
        href = link["href"].lower()
        if "whatsapp" in href and "whatsapp" not in str(result["evidence"]).lower():
            result["has_whatsapp"] = True
            result["evidence"].append("WhatsApp-Link im href")
            break

    # Strategie 4: "WhatsApp" Text im Kontaktbereich
    # Nur zaehlen wenn es in der Naehe von Kontakt-Woertern steht
    if not result["has_whatsapp"]:
        text = soup.get_text(separator=" ").lower()
        whatsapp_positions = [m.start() for m in re.finditer(r"whatsapp", text)]

        contact_words = [
            "kontakt", "erreichen", "schreib", "nachricht",
            "termin", "buchung", "anfrage", "chat", "erreichbar",
        ]

        for pos in whatsapp_positions:
            surrounding = text[max(0, pos - 100) : pos + 100]
            if any(w in surrounding for w in contact_words):
                result["has_whatsapp"] = True
                result["evidence"].append("WhatsApp-Erwaehnung im Kontaktbereich")
                break

    # Duplikate entfernen
    result["evidence"] = list(set(result["evidence"]))

    return result
