"""
Slack-Benachrichtigung nach Scraper-Run.

Sendet eine Summary-Nachricht und laedt die CSV-Dateien
als Datei in den konfigurierten Slack-Channel hoch.

Benoetigt:
    SLACK_BOT_TOKEN  - Bot User OAuth Token (xoxb-...)
    SLACK_CHANNEL_ID - Channel ID (z.B. C08XXXXXXXX)
"""

import os
import logging
from pathlib import Path

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    HAS_SLACK = True
except ImportError:
    HAS_SLACK = False


def send_slack_notification(
    leads_total: int,
    leads_with_email: int,
    leads_no_email: int,
    csv_email_path: str | None = None,
    csv_no_email_path: str | None = None,
    logger: logging.Logger | None = None,
) -> bool:
    """
    Sendet Scraper-Ergebnisse an Slack.

    1. Summary-Nachricht mit Zahlen
    2. CSV-Dateien als Upload

    Returns:
        True wenn erfolgreich, False wenn fehlgeschlagen oder nicht konfiguriert
    """
    if not logger:
        logger = logging.getLogger(__name__)

    if not HAS_SLACK:
        logger.warning("slack_sdk nicht installiert - pip install slack-sdk")
        return False

    token = os.getenv("SLACK_BOT_TOKEN", "")
    channel = os.getenv("SLACK_CHANNEL_ID", "")

    if not token or not channel:
        logger.info("Slack nicht konfiguriert (SLACK_BOT_TOKEN / SLACK_CHANNEL_ID fehlt) - ueberspringe")
        return False

    client = WebClient(token=token)

    # Summary-Nachricht
    summary = (
        f":mag: *APPOYNT Lead Scraper — fertig!*\n\n"
        f"• *{leads_total}* Leads gesamt\n"
        f"• *{leads_with_email}* mit E-Mail\n"
        f"• *{leads_no_email}* ohne E-Mail (Cold-Calling)\n"
    )

    try:
        client.chat_postMessage(channel=channel, text=summary)
        logger.info("Slack Summary gesendet")
    except SlackApiError as e:
        logger.error(f"Slack Nachricht fehlgeschlagen: {e.response['error']}")
        return False

    # CSV-Dateien hochladen
    for csv_path, label in [
        (csv_email_path, "Leads mit E-Mail"),
        (csv_no_email_path, "Leads ohne E-Mail (Cold-Calling)"),
    ]:
        if csv_path and Path(csv_path).exists() and Path(csv_path).stat().st_size > 0:
            try:
                client.files_upload_v2(
                    channel=channel,
                    file=str(csv_path),
                    title=label,
                    initial_comment=f":page_facing_up: {label}",
                )
                logger.info(f"CSV hochgeladen: {label}")
            except SlackApiError as e:
                logger.error(f"CSV Upload fehlgeschlagen ({label}): {e.response['error']}")

    return True
