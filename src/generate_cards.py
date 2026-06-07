import argparse
import base64
import datetime
import logging
import os
import re
import tempfile
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image
from rembg import new_session

from api_client import fetch_session_cards, fetch_sponsors
from gdrive_uploader import upload_output_folder
from image_processor import (
    composite_card,
    composite_speaker_video_card,
    composite_sponsor_card,
)
from models import SessionCard

logger = logging.getLogger(__name__)


def _slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s-]+", "-", slug).strip("-")
    return slug[:80]


def _parse_session_start(starts_at: str | None) -> datetime.datetime | None:
    if not starts_at:
        return None

    try:
        return datetime.datetime.fromisoformat(starts_at.replace("Z", "+00:00"))
    except ValueError:
        logger.warning("Unable to parse session start timestamp: %s", starts_at)
        return None


def _speaker_video_filename(card: SessionCard) -> str:
    start_at = _parse_session_start(card.starts_at)
    if start_at is None:
        logger.warning(
            "Missing session start timestamp for %s — falling back to current time",
            card.talk_title,
        )
        start_at = datetime.datetime.now()

    first_speaker = card.speakers[0].full_name if card.speakers else "unknown-speaker"
    timestamp = start_at.strftime("%d-%m-%Y-%H_%M")
    return f"{timestamp}-{_slugify(first_speaker)}.png"


def _output_paths(root_dir: Path) -> tuple[Path, Path, Path]:
    sessions_dir = root_dir / "sessions"
    pdf_tracks_dir = root_dir / "pdf-tracks"
    video_templates_dir = root_dir / "video-templates"

    sessions_dir.mkdir(parents=True, exist_ok=True)
    pdf_tracks_dir.mkdir(parents=True, exist_ok=True)
    video_templates_dir.mkdir(parents=True, exist_ok=True)

    return sessions_dir, pdf_tracks_dir, video_templates_dir


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
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

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
        default=str(datetime.date.today().year),
        help="Year for sponsors API (default: current year).",
    )
    args = parser.parse_args()

    load_dotenv()

    do_speakers = args.speakers
    do_sponsors = args.sponsors
    do_pdf = args.pdf

    if not do_speakers and not do_sponsors and not do_pdf:
        do_speakers = True
        do_sponsors = True
        do_pdf = True

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    sessions_dir, pdf_tracks_dir, video_templates_dir = _output_paths(output_dir)

    if do_speakers:
        api_slug = os.getenv("SESSIONIZE_API_SLUG")
        if not api_slug:
            logger.error("SESSIONIZE_API_SLUG is not set — cannot generate speaker cards")
            return
        _process_speakers(api_slug, sessions_dir, video_templates_dir)

    if do_sponsors:
        _process_sponsors(args.year, output_dir)

    if do_pdf:
        api_slug = os.getenv("SESSIONIZE_API_SLUG")
        if not api_slug:
            logger.error("SESSIONIZE_API_SLUG is not set — cannot generate PDFs")
            return
        _process_pdfs(api_slug, sessions_dir, pdf_tracks_dir)

    if args.upload:
        creds_path = _resolve_credentials_path()
        folder_id = os.getenv("GDRIVE_FOLDER_ID")

        if not creds_path or not folder_id:
            logger.error(
                "Upload requires GDRIVE_FOLDER_ID and either GDRIVE_CREDENTIALS_BASE64"
                " or GDRIVE_CREDENTIALS_PATH"
            )
            return

        logger.info("Uploading output directory to Google Drive (folder=%s)", folder_id)
        try:
            count = upload_output_folder(creds_path, folder_id, output_dir)
            logger.info("Google Drive upload complete: %d file(s) uploaded/updated", count)
        except Exception:
            logger.error("Google Drive upload failed", exc_info=True)


def _process_speakers(api_slug: str, sessions_dir: Path, video_templates_dir: Path) -> None:
    logger.info("Fetching sessions from Sessionize (slug=REDACTED)")
    try:
        cards = fetch_session_cards(api_slug)
        logger.info("Fetched %d sessions to process", len(cards))
    except Exception:
        logger.error("Failed to fetch sessions from Sessionize", exc_info=True)
        return

    bg_session = new_session()
    skipped = generated = errors = 0

    for i, card in enumerate(cards, 1):
        safe_name = _slugify(card.talk_title)
        logger.info("[%d/%d] Processing: %s", i, len(cards), card.talk_title)

        try:
            output_path_rm = sessions_dir / f"{safe_name}.png"
            output_path_bg = sessions_dir / f"{safe_name}_original.png"

            if not output_path_rm.exists():
                result_img_rm = composite_card(card, bg_session, remove_bg=True)
                if result_img_rm:
                    result_img_rm.save(output_path_rm)
                    logger.info("  Saved (bg removed): %s", output_path_rm.name)
                    generated += 1
                else:
                    logger.warning("  No output produced for: %s", card.talk_title)
            else:
                logger.debug("  Skipped (exists): %s", output_path_rm.name)
                skipped += 1

            if not output_path_bg.exists():
                result_img_bg = composite_card(card, bg_session, remove_bg=False)
                if result_img_bg:
                    result_img_bg.save(output_path_bg)
                    logger.info("  Saved (original): %s", output_path_bg.name)
                    generated += 1
                else:
                    logger.warning("  No output produced for: %s (original)", card.talk_title)
            else:
                logger.debug("  Skipped (exists): %s", output_path_bg.name)
                skipped += 1

            output_path_video = video_templates_dir / _speaker_video_filename(card)
            if not output_path_video.exists():
                result_img_video = composite_speaker_video_card(card)
                if result_img_video:
                    result_img_video.save(output_path_video)
                    logger.info("  Saved (speaker video): %s", output_path_video.name)
                    generated += 1
                else:
                    logger.warning("  No output produced for speaker video: %s", card.talk_title)
            else:
                logger.debug("  Skipped (exists): %s", output_path_video.name)
                skipped += 1

        except Exception:
            logger.error("Error generating card for: %s", card.talk_title, exc_info=True)
            errors += 1

    logger.info(
        "Speaker cards complete — generated=%d skipped=%d errors=%d",
        generated,
        skipped,
        errors,
    )


def _process_pdfs(api_slug: str, sessions_dir: Path, pdf_tracks_dir: Path) -> None:
    logger.info("Fetching sessions for PDF assembly (slug=REDACTED)")
    try:
        cards = fetch_session_cards(api_slug)
        logger.info("Fetched %d sessions", len(cards))
    except Exception:
        logger.error("Failed to fetch sessions for PDF assembly", exc_info=True)
        return

    track_images: dict[str, list[Path]] = defaultdict(list)
    track_images_orig: dict[str, list[Path]] = defaultdict(list)
    missing = 0

    for card in cards:
        safe_name = _slugify(card.talk_title)
        path_rm = sessions_dir / f"{safe_name}.png"
        path_orig = sessions_dir / f"{safe_name}_original.png"
        track_name = card.track or "Unknown Track"

        if path_rm.exists():
            track_images[track_name].append(path_rm)
        else:
            logger.debug("Missing card (bg removed): %s", path_rm.name)
            missing += 1

        if path_orig.exists():
            track_images_orig[track_name].append(path_orig)
        else:
            logger.debug("Missing card (original): %s", path_orig.name)

    if missing:
        logger.warning("%d session(s) have no generated card — PDFs may be incomplete", missing)

    all_tracks = set(track_images.keys()) | set(track_images_orig.keys())
    logger.info("Generating PDFs for %d track(s)", len(all_tracks))

    for track_name in sorted(all_tracks):
        safe_track = _slugify(track_name)

        if track_images[track_name]:
            _create_pdf(track_name, track_images[track_name], pdf_tracks_dir / f"{safe_track}.pdf")

        if track_images_orig[track_name]:
            _create_pdf(
                f"{track_name} (Original)",
                track_images_orig[track_name],
                pdf_tracks_dir / f"{safe_track}_original.pdf",
            )


def _create_pdf(label: str, image_paths: list[Path], pdf_path: Path) -> None:
    # Pillow 12+ uses lazy plugin loading; the PDF writer needs JPEG encoder registered
    Image.init()
    logger.info("Generating PDF: %s (%d image(s))", pdf_path.name, len(image_paths))
    try:
        images = []
        for img_path in image_paths:
            with Image.open(img_path) as img:
                images.append(img.convert("RGB").copy())

        if images:
            images[0].save(pdf_path, save_all=True, append_images=images[1:], resolution=100.0)
            logger.info("  Saved PDF: %s (%.1f KB)", pdf_path.name, pdf_path.stat().st_size / 1024)

            for im in images:
                im.close()
        else:
            logger.warning("  No images found for PDF track: %s", label)
    except Exception:
        logger.error("Failed to generate PDF for track: %s", label, exc_info=True)


def _process_sponsors(year: str, output_dir: Path) -> None:
    logger.info("Fetching sponsors for year %s", year)
    try:
        sponsors = fetch_sponsors(year)
        logger.info("Fetched %d sponsors", len(sponsors))
    except Exception:
        logger.error("Failed to fetch sponsors for year %s", year, exc_info=True)
        return

    skipped = generated = errors = 0

    for i, sponsor in enumerate(sponsors, 1):
        safe_name = _slugify(sponsor.name)
        output_path = output_dir / f"sponsor-{year}_{safe_name}.png"

        if output_path.exists():
            logger.debug("  Skipped (exists): %s", output_path.name)
            skipped += 1
            continue

        logger.info("[%d/%d] Generating sponsor card: %s", i, len(sponsors), sponsor.name)
        try:
            result_img = composite_sponsor_card(sponsor)
            if result_img:
                result_img.save(output_path)
                logger.info("  Saved: %s", output_path.name)
                generated += 1
            else:
                logger.warning("  No output produced for sponsor: %s", sponsor.name)
                errors += 1
        except Exception:
            logger.error("Error generating sponsor card: %s", sponsor.name, exc_info=True)
            errors += 1

    logger.info(
        "Sponsor cards complete — generated=%d skipped=%d errors=%d",
        generated,
        skipped,
        errors,
    )


if __name__ == "__main__":
    main()
