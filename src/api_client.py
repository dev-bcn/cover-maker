import logging
import os

import requests

from models import SessionCard, Speaker, Sponsor

logger = logging.getLogger(__name__)

SESSIONIZE_BASE_URL = "https://sessionize.com/api/v2"


def fetch_session_cards(api_slug: str) -> list[SessionCard]:
    url = f"{SESSIONIZE_BASE_URL}/{api_slug}/view/All"
    logger.debug("GET %s", url.replace(api_slug, "REDACTED"))
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()

    speaker_lookup: dict[str, Speaker] = {}
    for speaker_data in data.get("speakers", []):
        speaker_id = speaker_data.get("id")
        speaker_lookup[speaker_id] = Speaker(
            id=speaker_id,
            full_name=speaker_data.get("fullName", ""),
            profile_picture_url=speaker_data.get("profilePicture", ""),
        )

    track_lookup: dict[int, str] = {}
    for cat in data.get("categories", []):
        if "Track" in cat.get("title", ""):
            for item in cat.get("items", []):
                track_lookup[item.get("id")] = item.get("name")

    cards: list[SessionCard] = []
    for session_data in data.get("sessions", []):
        if session_data.get("isServiceSession") or session_data.get("isPlenumSession"):
            continue

        session_speakers = []
        for speaker_id in session_data.get("speakers", []):
            if speaker_id in speaker_lookup:
                session_speakers.append(speaker_lookup[speaker_id])

        session_track = None
        for cat_item in session_data.get("categoryItems", []):
            if cat_item in track_lookup:
                session_track = track_lookup[cat_item]
                break

        if session_speakers:
            cards.append(
                SessionCard(
                    talk_title=session_data.get("title", ""),
                    speakers=tuple(session_speakers),
                    track=session_track,
                )
            )

    logger.info(
        "Sessionize: %d sessions parsed (%d speakers, %d tracks)",
        len(cards),
        len(speaker_lookup),
        len(track_lookup),
    )
    return cards


def fetch_sponsors(year: str = "2026") -> list[Sponsor]:
    token = os.getenv("API_AUTH_TOKEN", "")
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        logger.warning("API_AUTH_TOKEN is not set — request may be rejected")

    url = f"https://www.devbcn.com/api/sponsors/{year}"
    logger.debug("GET %s", url)
    response = requests.get(url, headers=headers, timeout=30)

    if response.status_code == 401:
        logger.error("Sponsors API returned 401 Unauthorized — check API_AUTH_TOKEN secret")
    elif response.status_code == 404:
        logger.error("Sponsors API returned 404 — year %s may not exist yet", year)

    response.raise_for_status()
    data = response.json()

    sponsors = [
        Sponsor(
            name=item.get("name", ""),
            category=item.get("category", ""),
            logo_url=item.get("image", ""),
        )
        for item in data
    ]
    logger.info("Sponsors API: %d sponsors fetched for year %s", len(sponsors), year)
    return sponsors
