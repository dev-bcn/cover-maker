# DevBcn Speaker Card Generator

Automated pipeline for generating conference speaker cards by fetching data from Sessionize, removing backgrounds from profile pictures, and compositing them onto a custom template.

## Features

- **Automated Fetching**: Retrieves session and speaker data directly from Sessionize.
- **Background Removal**: Cleanly removes backgrounds using `rembg`.
- **Dual Layout Support**: Automatically handles single and dual speaker sessions.
- **Google Drive Integration**: Optional upload of generated cards to a shared Google Drive folder.
- **CI/CD**: Daily automated runs via GitHub Actions for always-up-to-date speaker cards.

## Prerequisites

- **Python 3.11+**
- **uv** (recommended for dependency management)

## Setup

1. **Install dependencies**:

   ```bash
   uv sync
   ```

2. **Configure Environment**:

   Copy `.env.example` to `.env` and fill in your credentials:
   - `SESSIONIZE_API_SLUG`: Your conference's Sessionize slug.
   - `GDRIVE_CREDENTIALS_PATH`: (Optional) Path to your Google Service Account JSON key.
   - `GDRIVE_FOLDER_ID`: (Optional) Target Google Drive folder ID.

3. **Assets**:

   Ensure your `assets/` directory contains:
   - `base_template.png`: The background template (standard size: 1080x1350).
   - `DejaVuSans.ttf`: The font used for rendering text.

## Usage

### Local Generation

Generate cards locally into the `output/` folder:

```bash
uv run python src/generate_cards.py
```

### Local Generation with Upload

Download data, generate cards, and push them to Google Drive:

```bash
uv run python src/generate_cards.py --upload
```

### Automation

The project includes a GitHub Actions workflow in `.github/workflows/generate-cards.yml` that runs daily at **06:00 UTC**.

To use it, set the following secrets in your GitHub repository:

- `SESSIONIZE_API_SLUG`
- `GDRIVE_CREDENTIALS_JSON` (the full content of your Service Account JSON)
- `GDRIVE_FOLDER_ID`

## Testing

Run the suite with coverage:

```bash
PYTHONPATH=src uv run pytest tests/ -v
```
