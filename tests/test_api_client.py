import responses

from src.api_client import SESSIONIZE_BASE_URL, fetch_session_cards


def test_fetch_returns_correct_cards(mock_sessionize_response: dict) -> None:
    api_slug = "test-slug"
    url = f"{SESSIONIZE_BASE_URL}/{api_slug}/view/All"

    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, url, json=mock_sessionize_response, status=200)

        cards = fetch_session_cards(api_slug)

        assert len(cards) == 2  # Should skip service and plenum
        assert cards[0].talk_title == "Single Speaker Talk"
        assert len(cards[0].speakers) == 1
        assert cards[0].speakers[0].full_name == "Speaker One"

        assert cards[1].talk_title == "Dual Speaker Talk"
        assert len(cards[1].speakers) == 2
        assert cards[1].speakers[0].full_name == "Speaker One"
        assert cards[1].speakers[1].full_name == "Speaker Two"


def test_fetch_skips_unconfirmed_speakers(mock_sessionize_response: dict) -> None:
    # If a session has a speaker not in the speaker lookup, it should be skipped
    # (actually handled in the code by the `if speaker_id in speaker_lookup` check)
    api_slug = "test-slug"
    url = f"{SESSIONIZE_BASE_URL}/{api_slug}/view/All"

    # Add a session with an unknown speaker
    mock_sessionize_response["sessions"].append(
        {
            "id": "s5",
            "title": "Unknown Speaker Talk",
            "isServiceSession": False,
            "isPlenumSession": False,
            "speakers": ["unknown-uuid"],
        }
    )

    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, url, json=mock_sessionize_response, status=200)
        cards = fetch_session_cards(api_slug)

        # Still only 2 valid cards with speakers
        assert len(cards) == 2
