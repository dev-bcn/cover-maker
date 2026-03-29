from unittest.mock import MagicMock, patch

import pytest

from src.gdrive_uploader import upload_output_folder


@pytest.fixture
def mock_google_drive():
    creds_patch = patch(
        "src.gdrive_uploader.service_account.Credentials.from_service_account_file"
    )
    build_patch = patch("src.gdrive_uploader.build")
    media_patch = patch("src.gdrive_uploader.MediaFileUpload")

    with creds_patch as mock_creds, build_patch as mock_build, media_patch as mock_media:
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        yield {
            "service": mock_service,
            "creds": mock_creds,
            "media": mock_media,
        }


def test_upload_output_folder_empty(tmp_path, mock_google_drive):
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    mock_service = mock_google_drive["service"]
    mock_service.files().list().execute.return_value = {"files": []}

    count = upload_output_folder("fake_creds.json", "fake_folder_id", output_dir)

    assert count == 0


def test_upload_output_folder_new_files(tmp_path, mock_google_drive):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "card1.png").write_text("fake-data")
    (output_dir / "card2.png").write_text("fake-data")
    (output_dir / "readme.txt").write_text("not-a-png")

    mock_service = mock_google_drive["service"]
    mock_service.files().list().execute.return_value = {"files": []}

    count = upload_output_folder("fake_creds.json", "fake_folder_id", output_dir)

    assert count == 2
    assert mock_service.files().create.call_count == 2
    assert mock_service.files().update.call_count == 0


def test_upload_output_folder_update_existing(tmp_path, mock_google_drive):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "card1.png").write_text("fake-data")

    mock_service = mock_google_drive["service"]
    mock_service.files().list().execute.return_value = {
        "files": [{"id": "id123", "name": "card1.png"}]
    }

    count = upload_output_folder("fake_creds.json", "fake_folder_id", output_dir)

    assert count == 1
    assert mock_service.files().create.call_count == 0
    assert mock_service.files().update.call_count == 1
    mock_service.files().update.assert_called_with(
        fileId="id123",
        media_body=mock_google_drive["media"].return_value,
        supportsAllDrives=True,
    )


def test_upload_output_folder_auth_failure(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    creds_patch = patch(
        "src.gdrive_uploader.service_account.Credentials.from_service_account_file",
        side_effect=Exception("Auth failed"),
    )
    with creds_patch:
        with pytest.raises(Exception, match="Auth failed"):
            upload_output_folder("fake_creds.json", "fake_folder_id", output_dir)
