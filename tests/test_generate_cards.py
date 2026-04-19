import json
import logging
import os
import unittest.mock as mock

import pytest
from PIL import Image

from src.generate_cards import _resolve_credentials_path, _slugify


def test_resolve_credentials_from_base64(monkeypatch, tmp_path) -> None:
    import base64

    fake_creds = json.dumps({"type": "service_account"})
    encoded = base64.b64encode(fake_creds.encode()).decode()

    monkeypatch.setenv("GDRIVE_CREDENTIALS_BASE64", encoded)
    monkeypatch.delenv("GDRIVE_CREDENTIALS_PATH", raising=False)

    result = _resolve_credentials_path()
    assert result is not None
    with open(result) as f:
        assert json.load(f) == {"type": "service_account"}
    os.unlink(result)


def test_resolve_credentials_from_path(monkeypatch) -> None:
    monkeypatch.delenv("GDRIVE_CREDENTIALS_BASE64", raising=False)
    monkeypatch.setenv("GDRIVE_CREDENTIALS_PATH", "/some/path.json")

    assert _resolve_credentials_path() == "/some/path.json"


def test_resolve_credentials_returns_none(monkeypatch) -> None:
    monkeypatch.delenv("GDRIVE_CREDENTIALS_BASE64", raising=False)
    monkeypatch.delenv("GDRIVE_CREDENTIALS_PATH", raising=False)

    assert _resolve_credentials_path() is None


def test_slugify() -> None:
    assert _slugify("Hello World") == "hello-world"
    assert _slugify("Multiple   Spaces   And - Dashes") == "multiple-spaces-and-dashes"
    assert _slugify("Special ! Characters ?") == "special-characters"
    assert _slugify("A" * 100) == "a" * 80


def test_main_with_sessions(tmp_path, monkeypatch, dummy_card_single, dummy_card_dual) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SESSIONIZE_API_SLUG", "test-slug")
    monkeypatch.setattr("sys.argv", ["src/generate_cards.py"])

    import src.generate_cards

    cards = [dummy_card_single, dummy_card_dual]
    with mock.patch("src.generate_cards.fetch_session_cards", return_value=cards):
        with mock.patch("src.generate_cards.new_session", return_value=None):
            with mock.patch(
                "src.generate_cards.composite_card", return_value=Image.new("RGB", (100, 100))
            ):
                src.generate_cards.main()

                assert os.path.isfile("output/single-talk.png")
                assert os.path.isfile("output/single-talk_original.png")
                assert os.path.isfile("output/dual-talk.png")


def test_main_with_upload(tmp_path, monkeypatch, dummy_card_single) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SESSIONIZE_API_SLUG", "test-slug")
    monkeypatch.setenv("GDRIVE_CREDENTIALS_PATH", "fake-creds.json")
    monkeypatch.setenv("GDRIVE_FOLDER_ID", "fake-folder-id")
    monkeypatch.setattr("sys.argv", ["src/generate_cards.py", "--upload"])

    import src.generate_cards

    with mock.patch("src.generate_cards.fetch_session_cards", return_value=[dummy_card_single]):
        with mock.patch("src.generate_cards.new_session", return_value=None):
            with mock.patch(
                "src.generate_cards.composite_card", return_value=Image.new("RGB", (100, 100))
            ):
                with mock.patch(
                    "src.generate_cards.upload_output_folder", return_value=1
                ) as mock_upload:
                    src.generate_cards.main()

                    mock_upload.assert_called_once_with(
                        "fake-creds.json", "fake-folder-id", mock.ANY
                    )


def test_main_upload_failure_is_logged(tmp_path, monkeypatch, caplog, dummy_card_single) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SESSIONIZE_API_SLUG", "test-slug")
    monkeypatch.setenv("GDRIVE_CREDENTIALS_PATH", "fake-creds.json")
    monkeypatch.setenv("GDRIVE_FOLDER_ID", "fake-folder-id")
    monkeypatch.setattr("sys.argv", ["src/generate_cards.py", "--upload"])

    import src.generate_cards

    with mock.patch("src.generate_cards.fetch_session_cards", return_value=[dummy_card_single]):
        with mock.patch("src.generate_cards.new_session", return_value=None):
            with mock.patch(
                "src.generate_cards.composite_card", return_value=Image.new("RGB", (100, 100))
            ):
                with mock.patch(
                    "src.generate_cards.upload_output_folder",
                    side_effect=RuntimeError("Drive error"),
                ):
                    with caplog.at_level(logging.ERROR, logger="src.generate_cards"):
                        src.generate_cards.main()

    assert any("Google Drive upload failed" in r.message for r in caplog.records)


def test_main_upload_missing_credentials_is_logged(tmp_path, monkeypatch, caplog) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SESSIONIZE_API_SLUG", "test-slug")
    monkeypatch.delenv("GDRIVE_CREDENTIALS_PATH", raising=False)
    monkeypatch.delenv("GDRIVE_CREDENTIALS_BASE64", raising=False)
    monkeypatch.delenv("GDRIVE_FOLDER_ID", raising=False)
    monkeypatch.setattr("sys.argv", ["src/generate_cards.py", "--upload"])

    import src.generate_cards

    with mock.patch("src.generate_cards.fetch_session_cards", return_value=[]):
        with mock.patch("src.generate_cards.new_session", return_value=None):
            with caplog.at_level(logging.ERROR, logger="src.generate_cards"):
                src.generate_cards.main()

    assert any("Upload requires" in r.message for r in caplog.records)


def test_main_no_slug(tmp_path, monkeypatch, caplog) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SESSIONIZE_API_SLUG", raising=False)
    monkeypatch.setattr("sys.argv", ["src/generate_cards.py"])

    import src.generate_cards

    with caplog.at_level(logging.ERROR, logger="src.generate_cards"):
        src.generate_cards.main()

    assert any("SESSIONIZE_API_SLUG" in r.message for r in caplog.records)


def test_main_fetch_error(tmp_path, monkeypatch, caplog) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SESSIONIZE_API_SLUG", "test-slug")
    monkeypatch.setattr("sys.argv", ["src/generate_cards.py", "--speakers"])

    import src.generate_cards

    with mock.patch("src.generate_cards.fetch_session_cards", side_effect=Exception("API Error")):
        with mock.patch("src.generate_cards.new_session", return_value=None):
            with caplog.at_level(logging.ERROR, logger="src.generate_cards"):
                src.generate_cards.main()

    assert any("Failed to fetch sessions" in r.message for r in caplog.records)


def test_sponsors_only_does_not_require_sessionize_slug(tmp_path, monkeypatch, caplog) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SESSIONIZE_API_SLUG", raising=False)
    monkeypatch.setattr("sys.argv", ["src/generate_cards.py", "--sponsors"])

    import src.generate_cards

    with mock.patch("src.generate_cards.fetch_sponsors", return_value=[]) as mock_sponsors:
        src.generate_cards.main()
        mock_sponsors.assert_called_once()

    assert not any("SESSIONIZE_API_SLUG" in r.message for r in caplog.records)


def test_process_sponsors_skips_existing(tmp_path, monkeypatch, caplog) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["src/generate_cards.py", "--sponsors", "--year", "2099"])

    import src.generate_cards
    from src.models import Sponsor

    sponsor = Sponsor(name="Acme Corp", category="Gold", logo_url="http://example.com/logo.png")
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "sponsor-2099_acme-corp.png").write_bytes(b"fake")

    with mock.patch("src.generate_cards.fetch_sponsors", return_value=[sponsor]):
        with caplog.at_level(logging.DEBUG, logger="src.generate_cards"):
            src.generate_cards._process_sponsors("2099", output_dir)

    assert any("Skipped" in r.message for r in caplog.records)


def test_process_sponsors_logs_error_on_failure(tmp_path, caplog) -> None:
    import src.generate_cards
    from src.models import Sponsor

    sponsor = Sponsor(name="Bad Corp", category="Silver", logo_url="http://bad.example/logo.png")
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    with mock.patch("src.generate_cards.fetch_sponsors", return_value=[sponsor]):
        with mock.patch(
            "src.generate_cards.composite_sponsor_card", side_effect=RuntimeError("render failed")
        ):
            with caplog.at_level(logging.ERROR, logger="src.generate_cards"):
                src.generate_cards._process_sponsors("2026", output_dir)

    assert any("Error generating sponsor card" in r.message for r in caplog.records)


@pytest.mark.parametrize("slug_env_set", [True, False])
def test_process_pdfs_warns_on_missing_cards(tmp_path, monkeypatch, caplog, slug_env_set) -> None:
    import src.generate_cards
    from src.models import SessionCard, Speaker

    card = SessionCard(
        talk_title="My Talk",
        speakers=(Speaker(id="1", full_name="Alice", profile_picture_url=""),),
        track="Test Track",
    )
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    with mock.patch("src.generate_cards.fetch_session_cards", return_value=[card]):
        with caplog.at_level(logging.WARNING, logger="src.generate_cards"):
            src.generate_cards._process_pdfs("slug", output_dir)

    assert any("incomplete" in r.message for r in caplog.records)
