import argparse
import base64
import os
import re
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from rembg import new_session

from api_client import fetch_session_cards
from gdrive_uploader import upload_output_folder
from image_processor import composite_card


def _slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s-]+", "-", slug).strip("-")
    return slug[:80]


def _resolve_credentials_path() -> str | None:
    b64_value = os.getenv("GDRIVE_CREDENTIALS_BASE64")
    if b64_value:
        decoded = base64.b64decode(b64_value)
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        tmp.write(decoded)
        tmp.close()
        return tmp.name

    return os.getenv("GDRIVE_CREDENTIALS_PATH")


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

    from collections import defaultdict

    from PIL import Image

    track_images = defaultdict(list)

    for i, card in enumerate(cards, 1):
        safe_name = _slugify(card.talk_title)

        print(f"[{i}/{len(cards)}] Generating card for: {card.talk_title}")

        track_name = card.track or "Unknown Track"

        try:
            if len(card.speakers) == 1:
                output_path_rm = output_dir / f"{safe_name}.png"
                output_path_bg = output_dir / f"{safe_name}_original.png"

                if not output_path_rm.exists():
                    result_img_rm = composite_card(card, bg_session, remove_bg=True)
                    result_img_rm.save(output_path_rm)
                    print(f"  Saved to: {output_path_rm}")
                else:
                    print(f"  Skipped (exists): {output_path_rm}")

                if not output_path_bg.exists():
                    result_img_bg = composite_card(card, bg_session, remove_bg=False)
                    result_img_bg.save(output_path_bg)
                    print(f"  Saved to: {output_path_bg}")
                else:
                    print(f"  Skipped (exists): {output_path_bg}")

                track_images[track_name].append(output_path_rm)
            else:
                output_path = output_dir / f"{safe_name}.png"
                if not output_path.exists():
                    result_img = composite_card(card, bg_session, remove_bg=True)
                    result_img.save(output_path)
                    print(f"  Saved to: {output_path}")
                else:
                    print(f"  Skipped (exists): {output_path}")

                track_images[track_name].append(output_path)
        except Exception as e:
            print(f"  Error generating card for {card.talk_title}: {e}")

    print("\nGenerating PDFs...")
    for track_name, image_paths in track_images.items():
        if not image_paths:
            continue
        safe_track = _slugify(track_name)
        pdf_path = output_dir / f"{safe_track}.pdf"
        print(f"Generating PDF for track: {track_name} -> {pdf_path}")

        try:
            images = []
            for img_path in image_paths:
                if img_path.exists():
                    images.append(Image.open(img_path).convert("RGB"))

            if images:
                images[0].save(pdf_path, save_all=True, append_images=images[1:], resolution=100.0)
                print(f"  Saved PDF: {pdf_path}")
        except Exception as e:
            print(f"  Error generating PDF for track {track_name}: {e}")

    # 4. Optional Upload
    if args.upload:
        creds_path = _resolve_credentials_path()
        folder_id = os.getenv("GDRIVE_FOLDER_ID")

        if not creds_path or not folder_id:
            print(
                "Error: GDRIVE_FOLDER_ID and either GDRIVE_CREDENTIALS_BASE64 or"
                " GDRIVE_CREDENTIALS_PATH must be set for upload."
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
