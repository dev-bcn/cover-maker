import logging
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


_UPLOAD_TYPES = [
    ("*.png", "image/png"),
    ("*.pdf", "application/pdf"),
]


def upload_output_folder(
    credentials_path: str, folder_id: str, output_dir: Path = Path("output")
) -> int:
    if not output_dir.exists():
        logger.warning(f"Output directory {output_dir} does not exist. Skipping upload.")
        return 0

    # 1. Authenticate
    try:
        creds = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=["https://www.googleapis.com/auth/drive"]
        )
        service = build("drive", "v3", credentials=creds)
    except Exception as e:
        logger.error(f"Failed to authenticate with Google Drive: {e}")
        raise

    # 2. Get existing files in folder to avoid duplicates (upsert logic)
    query = f"'{folder_id}' in parents and trashed = false"
    try:
        results = (
            service.files()
            .list(
                q=query,
                spaces="drive",
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
    except Exception as e:
        logger.error(f"Failed to list files in Google Drive folder {folder_id}: {e}")
        raise

    existing_files = {f["name"]: f["id"] for f in results.get("files", [])}

    upload_count = 0
    for glob_pattern, mimetype in _UPLOAD_TYPES:
        for file_path in sorted(output_dir.glob(glob_pattern)):
            file_name = file_path.name
            media = MediaFileUpload(str(file_path), mimetype=mimetype)

            try:
                if file_name in existing_files:
                    file_id = existing_files[file_name]
                    logger.info(f"Updating existing file: {file_name} (ID: {file_id})")
                    service.files().update(
                        fileId=file_id, media_body=media, supportsAllDrives=True
                    ).execute()
                else:
                    logger.info(f"Uploading new file: {file_name}")
                    file_metadata = {"name": file_name, "parents": [folder_id]}
                    service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields="id",
                        supportsAllDrives=True,
                    ).execute()

                upload_count += 1
            except Exception as e:
                logger.error(f"Error uploading {file_name}: {e}")

    return upload_count
