import argparse
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from rembg import new_session

from api_client import fetch_session_cards
from gdrive_uploader import upload_output_folder
from image_processor import composite_card


def _slugify(text: str) -> str:
    # Safe filename slugify
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s-]+", "-", slug).strip("-")
    return slug[:80]


def main() -> None:
    # 0. CLI Args
    parser = argparse.ArgumentParser(description="Generate speaker cards from Sessionize data.")
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload the generated cards to Google Drive after processing.",
    )
    args = parser.parse_args()

    # 1. Setup
    load_dotenv()
    api_slug = os.getenv("SESSIONIZE_API_SLUG")
    if not api_slug:
        print("Error: SESSIONIZE_API_SLUG not found in .env")
        return

    # 2. Fetch data
    print(f"Fetching sessions for slug: {api_slug}...")
    try:
        cards = fetch_session_cards(api_slug)
        print(f"Found {len(cards)} sessions to process.")
    except Exception as e:
        print(f"Error fetching sessions: {e}")
        return

    # 3. Process cards
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # One rembg session for all images to avoid reloading model
    bg_session = new_session()

    for i, card in enumerate(cards, 1):
        safe_name = _slugify(card.talk_title)
        output_path = output_dir / f"{safe_name}.png"

        print(f"[{i}/{len(cards)}] Generating card for: {card.talk_title}")

        try:
            result_img = composite_card(card, bg_session)
            result_img.save(output_path)
            print(f"  Saved to: {output_path}")
        except Exception as e:
            print(f"  Error generating card for {card.talk_title}: {e}")

    # 4. Optional Upload
    if args.upload:
        creds_path = os.getenv("GDRIVE_CREDENTIALS_PATH")
        folder_id = os.getenv("GDRIVE_FOLDER_ID")

        if not creds_path or not folder_id:
            print(
                "Error: GDRIVE_CREDENTIALS_PATH and GDRIVE_FOLDER_ID must be set in .env for upload."
            )
            return

        print("\nUploading to Google Drive...")
        try:
            count = upload_output_folder(creds_path, folder_id, output_dir)
            print(f"Successfully uploaded/updated {count} files in Google Drive.")
        except Exception as e:
            print(f"Error during Google Drive upload: {e}")


if __name__ == "__main__":
    main()
