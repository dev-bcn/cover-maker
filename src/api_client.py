import requests

from models import SessionCard, Speaker

SESSIONIZE_BASE_URL = "https://sessionize.com/api/v2"


def fetch_session_cards(api_slug: str) -> list[SessionCard]:
    url = f"{SESSIONIZE_BASE_URL}/{api_slug}/view/All"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    # Map speakers by ID
    speaker_lookup: dict[str, Speaker] = {}
    for speaker_data in data.get("speakers", []):
        speaker_id = speaker_data.get("id")
        speaker_lookup[speaker_id] = Speaker(
            id=speaker_id,
            full_name=speaker_data.get("fullName", ""),
            profile_picture_url=speaker_data.get("profilePicture", ""),
        )

    cards: list[SessionCard] = []
    for session_data in data.get("sessions", []):
        # Skip service and plenum sessions
        if session_data.get("isServiceSession") or session_data.get("isPlenumSession"):
            continue

        session_speakers = []
        for speaker_id in session_data.get("speakers", []):
            if speaker_id in speaker_lookup:
                session_speakers.append(speaker_lookup[speaker_id])

        if session_speakers:
            cards.append(
                SessionCard(
                    talk_title=session_data.get("title", ""), speakers=tuple(session_speakers)
                )
            )

    return cards
