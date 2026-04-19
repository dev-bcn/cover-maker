import logging
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

_UPLOAD_TYPES = [
    ("*.png", "image/png"),
    ("*.pdf", "application/pdf"),
]


def upload_output_folder(
    credentials_path: str, folder_id: str, output_dir: Path = Path("output")
) -> int:
    if not output_dir.exists():
        logger.warning("Output directory %s does not exist — skipping upload", output_dir)
        return 0

    try:
        creds = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=["https://www.googleapis.com/auth/drive"]
        )
        service = build("drive", "v3", credentials=creds)
        logger.info("Authenticated with Google Drive service account")
    except Exception:
        logger.error("Failed to authenticate with Google Drive", exc_info=True)
        raise

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
    except Exception:
        logger.error("Failed to list files in Drive folder %s", folder_id, exc_info=True)
        raise

    existing_files = {f["name"]: f["id"] for f in results.get("files", [])}
    logger.info("Found %d existing file(s) in Drive folder", len(existing_files))

    upload_count = 0
    error_count = 0

    for glob_pattern, mimetype in _UPLOAD_TYPES:
        files = sorted(output_dir.glob(glob_pattern))
        if not files:
            logger.debug("No files matched pattern %s in %s", glob_pattern, output_dir)
            continue

        logger.info("Uploading %d file(s) matching %s", len(files), glob_pattern)
        for file_path in files:
            file_name = file_path.name
            file_size_kb = file_path.stat().st_size / 1024
            media = MediaFileUpload(str(file_path), mimetype=mimetype)

            try:
                if file_name in existing_files:
                    file_id = existing_files[file_name]
                    logger.info("Updating: %s (%.1f KB, ID=%s)", file_name, file_size_kb, file_id)
                    service.files().update(
                        fileId=file_id, media_body=media, supportsAllDrives=True
                    ).execute()
                else:
                    logger.info("Uploading new: %s (%.1f KB)", file_name, file_size_kb)
                    file_metadata = {"name": file_name, "parents": [folder_id]}
                    service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields="id",
                        supportsAllDrives=True,
                    ).execute()

                upload_count += 1
            except Exception:
                logger.error("Failed to upload %s", file_name, exc_info=True)
                error_count += 1

    logger.info("Drive upload complete — uploaded=%d errors=%d", upload_count, error_count)
    return upload_count
