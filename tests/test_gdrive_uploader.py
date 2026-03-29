from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from src.gdrive_uploader import upload_output_folder


@pytest.fixture
def mock_google_drive():
    with patch("src.gdrive_uploader.service_account.Credentials.from_service_account_file") as mock_creds, \
         patch("src.gdrive_uploader.build") as mock_build, \
         patch("src.gdrive_uploader.MediaFileUpload") as mock_media:
        
        # Mocking the service object
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        yield {
            "service": mock_service,
            "creds": mock_creds,
            "media": mock_media
        }


def test_upload_output_folder_empty(tmp_path, mock_google_drive):
    # Setup
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Mock list response
    mock_service = mock_google_drive["service"]
    mock_service.files().list().execute.return_value = {"files": []}
    
    # Run
    count = upload_output_folder("fake_creds.json", "fake_folder_id", output_dir)
    
    # Verify
    assert count == 0


def test_upload_output_folder_new_files(tmp_path, mock_google_drive):
    # Setup
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "card1.png").write_text("fake-data")
    (output_dir / "card2.png").write_text("fake-data")
    (output_dir / "readme.txt").write_text("not-a-png")
    
    # Mock list response (empty folder initially)
    mock_service = mock_google_drive["service"]
    mock_service.files().list().execute.return_value = {"files": []}
    
    # Run
    count = upload_output_folder("fake_creds.json", "fake_folder_id", output_dir)
    
    # Verify
    assert count == 2
    assert mock_service.files().create.call_count == 2
    assert mock_service.files().update.call_count == 0


def test_upload_output_folder_update_existing(tmp_path, mock_google_drive):
    # Setup
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "card1.png").write_text("fake-data")
    
    # Mock list response (file already exists)
    mock_service = mock_google_drive["service"]
    mock_service.files().list().execute.return_value = {
        "files": [{"id": "id123", "name": "card1.png"}]
    }
    
    # Run
    count = upload_output_folder("fake_creds.json", "fake_folder_id", output_dir)
    
    # Verify
    assert count == 1
    assert mock_service.files().create.call_count == 0
    assert mock_service.files().update.call_count == 1
    mock_service.files().update.assert_called_with(
        fileId="id123", media_body=mock_google_drive["media"].return_value
    )


def test_upload_output_folder_auth_failure(tmp_path):
    # Setup
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    with patch("src.gdrive_uploader.service_account.Credentials.from_service_account_file", side_effect=Exception("Auth failed")):
        with pytest.raises(Exception, match="Auth failed"):
            upload_output_folder("fake_creds.json", "fake_folder_id", output_dir)
