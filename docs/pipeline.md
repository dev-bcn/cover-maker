# Speaker Card Generator Pipeline

This document describes the data flow and logic of the speaker card generation pipeline.

## Overview

The pipeline automates the creation of conference speaker cards by fetching data from Sessionize, removing backgrounds from speaker photos, and compositing them onto a template with word-wrapped title text.

## Modules

### `src/api_client.py`

- Fetches all data in a single request from the `/view/All` Sessionize endpoint.
- Maps speaker data to `Speaker` dataclasses.
- Filters and maps session data to `SessionCard` dataclasses.
- Skips service and plenum sessions.

### `src/image_processor.py`

- **Background Removal**: Uses `rembg` with a shared session to efficiently remove backgrounds from profile pictures.
- **Normalization**: Crops transparent margins and resizes the subject to a standardized height (`500px`).
- **Compositing**:
  - Handles single and dual speaker layouts.
  - Positions subjects relative to an anchor line.
  - Uses alpha channels as masks for clean blending.
- **Text Rendering**:
  - join speaker names with " & ".
  - Word-wraps the talk title to fit within safe margins.
  - Applies a drop-shadow effect for legibility.

### `src/gdrive_uploader.py`

- **Authentication**: Uses Google Service Account JSON credentials.
- **Upsert Logic**: Searches for existing files by name in the target folder.
  - If found: Updates the existing file.
  - If not found: Uploads as a new file.
- **MIME Type**: Enforces `image/png` for all uploads.

### `src/generate_cards.py`

- Entry point that orchestrates the workflow.
- Loads configuration from `.env`.
- Iterates over session cards and saves the final PNGs to the `output/` directory.

## Requirements

- Python 3.11+
- `uv` for dependency management.
- ML model for `rembg` (downloaded automatically on first run, ~170MB).

## Usage

1. Place `base_template.png` and your font file in `assets/`.
2. Configure coordinates in `src/image_processor.py`.
3. Set `SESSIONIZE_API_SLUG` in `.env`.
4. Run: `uv run python src/generate_cards.py`.
5. For upload: `uv run python src/generate_cards.py --upload` (requires `.env` config).

## CI/CD Automation

A GitHub Actions workflow (`.github/workflows/generate-cards.yml`) is configured to run daily at 06:00 UTC.

### Required GitHub Secrets

- `SESSIONIZE_API_SLUG`: The Sessionize API slug.
- `GDRIVE_CREDENTIALS_JSON`: The full JSON content of the Google Service Account key.
- `GDRIVE_FOLDER_ID`: The ID of the target Google Drive folder.

### Automation Logic

1. **Caching**: Uses `setup-uv` to cache Python dependencies based on `uv.lock`.
2. **Ephemeral Credentials**: The `GDRIVE_CREDENTIALS_JSON` secret is written to `/tmp/gdrive-creds.json` during the run and deleted afterward.
3. **Daily Generation**: Automatically fetches current data from Sessionize and refreshes the cards in Google Drive.
