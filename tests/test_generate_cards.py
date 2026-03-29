import os

from PIL import Image

from src.generate_cards import _slugify


def test_slugify() -> None:
    assert _slugify("Hello World") == "hello-world"
    assert _slugify("Multiple   Spaces   And - Dashes") == "multiple-spaces-and-dashes"
    assert _slugify("Special ! Characters ?") == "special-characters"
    assert _slugify("A" * 100) == "a" * 80  # Max length 80


def test_main_with_sessions(tmp_path, monkeypatch, dummy_card_single) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SESSIONIZE_API_SLUG", "test-slug")
    monkeypatch.setattr("sys.argv", ["src/generate_cards.py"])

    import unittest.mock as mock

    import src.generate_cards

    # Mock all external dependencies
    with mock.patch("src.generate_cards.fetch_session_cards", return_value=[dummy_card_single]):
        with mock.patch("src.generate_cards.new_session", return_value=None):
            with mock.patch(
                "src.generate_cards.composite_card", return_value=Image.new("RGB", (100, 100))
            ):
                src.generate_cards.main()

                # Check output file exists
                assert os.path.isfile("output/single-talk.png")


def test_main_with_upload(tmp_path, monkeypatch, dummy_card_single) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SESSIONIZE_API_SLUG", "test-slug")
    monkeypatch.setenv("GDRIVE_CREDENTIALS_PATH", "fake-creds.json")
    monkeypatch.setenv("GDRIVE_FOLDER_ID", "fake-folder-id")
    monkeypatch.setattr("sys.argv", ["src/generate_cards.py", "--upload"])

    import unittest.mock as mock

    import src.generate_cards

    # Mock all external dependencies
    with mock.patch("src.generate_cards.fetch_session_cards", return_value=[dummy_card_single]):
        with mock.patch("src.generate_cards.new_session", return_value=None):
            with mock.patch(
                "src.generate_cards.composite_card", return_value=Image.new("RGB", (100, 100))
            ):
                with mock.patch("src.generate_cards.upload_output_folder", return_value=1) as mock_upload:
                    src.generate_cards.main()

                    # Verify upload was called
                    mock_upload.assert_called_once_with("fake-creds.json", "fake-folder-id", mock.ANY)


def test_main_no_slug(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SESSIONIZE_API_SLUG", raising=False)
    monkeypatch.setattr("sys.argv", ["src/generate_cards.py"])

    import src.generate_cards

    src.generate_cards.main()

    captured = capsys.readouterr()
    assert "SESSIONIZE_API_SLUG not found" in captured.out


def test_main_fetch_error(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SESSIONIZE_API_SLUG", "test-slug")
    monkeypatch.setattr("sys.argv", ["src/generate_cards.py"])

    import unittest.mock as mock

    import src.generate_cards

    with mock.patch("src.generate_cards.fetch_session_cards", side_effect=Exception("API Error")):
        src.generate_cards.main()

    captured = capsys.readouterr()
    assert "Error fetching sessions: API Error" in captured.out
