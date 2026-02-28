from __future__ import annotations

"""
Sales-Opener-Generator fuer APPOYNT Cold Calls.

Erstellt personalisierte Kaltakquise-Eroeffnungen basierend auf den
erkannten Website-Signalen. Vier Szenarien basierend auf der
2x2-Matrix: WhatsApp ja/nein x Buchungssystem ja/nein.

Alle Texte auf Deutsch (Zielmarkt Deutschland).
"""


def generate_sales_opener(
    business_name: str,
    has_whatsapp: bool,
    has_booking_system: bool,
    booking_system_name: str,
    has_generic_booking: bool,
    google_rating: float | str,
    google_reviews: int | str,
    category_label: str,
) -> str:
    """
    Generiert einen personalisierten Cold-Call-Opener.

    Die 4 Szenarien:
    1. WhatsApp JA + Booking JA  -> Tech-affin, Pitch: Integration/Verbesserung
    2. WhatsApp JA + Booking NEIN -> Nutzen WA, aber buchen manuell -> Pitch: Automatisierung
    3. WhatsApp NEIN + Booking JA -> Haben Booking, verpassen WA-Kanal -> Pitch: WA-Kanal
    4. WhatsApp NEIN + Booking NEIN -> Brauchen alles -> Full Pitch

    Args:
        business_name: Name des Businesses
        has_whatsapp: WhatsApp erkannt?
        has_booking_system: Buchungssystem erkannt?
        booking_system_name: Name des Systems (z.B. "Calendly")
        has_generic_booking: Nur generischer "Termin buchen" Button?
        google_rating: Google-Bewertung (z.B. 4.7)
        google_reviews: Anzahl Google-Bewertungen
        category_label: Branche (z.B. "Friseur / Friseursalon")

    Returns:
        Deutscher Opener-Text als String
    """
    # Rating-Kompliment erstellen (nur bei guten Bewertungen)
    rating_line = _build_rating_line(business_name, google_rating, google_reviews)

    # Szenario 1: WhatsApp JA + Buchungssystem JA
    if has_whatsapp and (has_booking_system or has_generic_booking):
        system_ref = f" ueber {booking_system_name}" if booking_system_name else ""
        return (
            f"{rating_line}"
            f"Ich sehe, dass Sie bereits WhatsApp fuer die Kundenkommunikation nutzen "
            f"und Termine{system_ref} anbieten. "
            f"Wir verbinden beides: Ihre Kunden koennen direkt per WhatsApp "
            f"Termine buchen - ohne App-Wechsel, ohne Wartezeit. "
            f"Darf ich Ihnen kurz zeigen, wie das fuer {business_name} aussehen wuerde?"
        )

    # Szenario 2: WhatsApp JA + Kein Buchungssystem
    if has_whatsapp and not has_booking_system:
        return (
            f"{rating_line}"
            f"Ich sehe, dass Sie WhatsApp bereits fuer die Kundenkommunikation nutzen - "
            f"das ist super. Viele Ihrer Kunden schreiben Ihnen wahrscheinlich schon "
            f"per WhatsApp wegen Terminen, und Sie antworten dann manuell. "
            f"Wir koennen das automatisieren: Kunden buchen direkt im WhatsApp-Chat "
            f"einen freien Termin, und Sie bekommen nur noch die Bestaetigung. "
            f"Haetten Sie kurz Zeit, dass ich Ihnen zeige wie das fuer {business_name} funktioniert?"
        )

    # Szenario 3: Kein WhatsApp + Buchungssystem JA
    if not has_whatsapp and (has_booking_system or has_generic_booking):
        system_ref = f"mit {booking_system_name} " if booking_system_name else ""
        return (
            f"{rating_line}"
            f"Ich sehe, dass Sie {system_ref}bereits Online-Terminbuchung anbieten - sehr gut. "
            f"Wussten Sie, dass ueber 80% der Deutschen taeglich WhatsApp nutzen? "
            f"Wir ermoeglichen Ihren Kunden, Termine direkt per WhatsApp zu buchen, "
            f"ohne eine extra Website oder App oeffnen zu muessen. "
            f"Das erhoeht die Buchungsrate deutlich. "
            f"Darf ich Ihnen zeigen, wie das fuer {business_name} funktionieren wuerde?"
        )

    # Szenario 4: Kein WhatsApp + Kein Buchungssystem
    return (
        f"{rating_line}"
        f"Aktuell buchen Ihre Kunden Termine wahrscheinlich per Telefon oder "
        f"persoenlich vor Ort. Das kostet Sie und Ihr Team wertvolle Zeit. "
        f"Wir ermoeglichen Ihren Kunden, Termine rund um die Uhr per WhatsApp zu buchen - "
        f"automatisch, ohne dass jemand ans Telefon muss. "
        f"Haetten Sie kurz Zeit fuer eine Demo, wie das fuer {business_name} aussehen kann?"
    )


def _build_rating_line(
    business_name: str,
    google_rating: float | str,
    google_reviews: int | str,
) -> str:
    """
    Erstellt einen Kompliment-Satz basierend auf Google-Bewertungen.
    Nur bei wirklich guten Bewertungen (>= 4.0 mit >= 20 Reviews).
    """
    try:
        rating = float(google_rating) if google_rating else 0
        reviews = int(google_reviews) if google_reviews else 0
    except (ValueError, TypeError):
        return ""

    if rating >= 4.5 and reviews >= 50:
        return (
            f"Ich habe gesehen, dass {business_name} mit {rating} Sternen "
            f"bei {reviews} Bewertungen hervorragend bewertet ist. "
        )
    elif rating >= 4.0 and reviews >= 20:
        return (
            f"{business_name} hat starke {rating} Sterne bei Google - "
            f"das zeigt, dass Ihre Kunden sehr zufrieden sind. "
        )

    return ""
