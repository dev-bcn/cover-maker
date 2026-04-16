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
    parser.add_argument(
        "--speakers",
        action="store_true",
        help="Generate speaker cards (default behavior if no flags are passed).",
    )
    parser.add_argument(
        "--sponsors",
        action="store_true",
        help="Generate sponsor cards.",
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Generate track PDFs from existing/generated speaker cards.",
    )
    parser.add_argument(
        "--year",
        default="2026",
        help="Year for sponsors API (default: 2026).",
    )
    args = parser.parse_args()

    # 1. Setup
    load_dotenv()
    api_slug = os.getenv("SESSIONIZE_API_SLUG")
    if not api_slug:
        print("Error: SESSIONIZE_API_SLUG not found in .env")
        return

    do_speakers = args.speakers
    do_sponsors = args.sponsors
    do_pdf = args.pdf

    if not do_speakers and not do_sponsors and not do_pdf:
        # Default behavior: run everything
        do_speakers = True
        do_sponsors = True
        do_pdf = True

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    if do_speakers:
        _process_speakers(api_slug, output_dir)

    if do_sponsors:
        _process_sponsors(args.year, output_dir)

    if do_pdf:
        _process_pdfs(api_slug, output_dir)

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


def _process_speakers(api_slug: str, output_dir: Path) -> None:
    print(f"\nFetching sessions for slug: {api_slug}...")
    try:
        cards = fetch_session_cards(api_slug)
        print(f"Found {len(cards)} sessions to process.")
    except Exception as e:
        print(f"Error fetching sessions: {e}")
        return

    # One rembg session for all images to avoid reloading model
    bg_session = new_session()

    for i, card in enumerate(cards, 1):
        safe_name = _slugify(card.talk_title)
        print(f"[{i}/{len(cards)}] Generating card for: {card.talk_title}")

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
            else:
                output_path = output_dir / f"{safe_name}.png"
                if not output_path.exists():
                    result_img = composite_card(card, bg_session, remove_bg=True)
                    result_img.save(output_path)
                    print(f"  Saved to: {output_path}")
                else:
                    print(f"  Skipped (exists): {output_path}")

        except Exception as e:
            print(f"  Error generating card for {card.talk_title}: {e}")


def _process_pdfs(api_slug: str, output_dir: Path) -> None:
    from PIL import Image
    from collections import defaultdict

    print(f"\nFetching sessions for PDFs (slug: {api_slug})...")
    try:
        cards = fetch_session_cards(api_slug)
    except Exception as e:
        print(f"Error fetching sessions for PDFs: {e}")
        return

    track_images = defaultdict(list)
    for card in cards:
        safe_name = _slugify(card.talk_title)
        output_path = output_dir / f"{safe_name}.png"
        track_name = card.track or "Unknown Track"
        if output_path.exists():
            track_images[track_name].append(output_path)

    print("\nGenerating PDFs from existing speaker cards...")
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
                # resolution=100.0 is used in the original code
                images[0].save(pdf_path, save_all=True, append_images=images[1:], resolution=100.0)
                print(f"  Saved PDF: {pdf_path}")
        except Exception as e:
            print(f"  Error generating PDF for track {track_name}: {e}")


def _process_sponsors(year: str, output_dir: Path) -> None:
    from api_client import fetch_sponsors
    from image_processor import composite_sponsor_card

    print(f"\nFetching sponsors for year {year}...")
    try:
        sponsors = fetch_sponsors(year)
        print(f"Found {len(sponsors)} sponsors to process.")
    except Exception as e:
        print(f"Error fetching sponsors: {e}")
        return

    print("\nGenerating sponsor cards...")
    for i, sponsor in enumerate(sponsors, 1):
        safe_name = _slugify(sponsor.name)
        output_path = output_dir / f"sponsor-{year}_{safe_name}.png"

        if output_path.exists():
            print(f"  Skipped (exists): {output_path}")
            continue

        print(f"[{i}/{len(sponsors)}] Generating card for: {sponsor.name}")
        try:
            result_img = composite_sponsor_card(sponsor)
            result_img.save(output_path)
            print(f"  Saved to: {output_path}")
        except Exception as e:
            print(f"  Error processing sponsor {sponsor.name}: {e}")


if __name__ == "__main__":
    main()
