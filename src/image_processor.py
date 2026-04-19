import logging
from io import BytesIO
from pathlib import Path

import requests
import resvg_py
from PIL import Image, ImageDraw, ImageFont
from rembg import remove

from models import SessionCard, Sponsor

# Setup module-level logger
logger = logging.getLogger(__name__)

# Module-level constants (fill in values after placing assets)
TEMPLATE_PATH: Path = Path("assets") / "base_template.png"
FONT_PATH: Path = Path("assets") / "DejaVuSans.ttf"

# Layout — pixel coordinates relative to template canvas
SPEAKER_TARGET_HEIGHT: int = 500  # normalized height of each speaker cutout
SPEAKER_ANCHOR_Y: int = 820  # PLACEHOLDER: y-pixel where speaker bottom aligns
SPEAKER_SINGLE_X: int = 270  # PLACEHOLDER: x for single-speaker card
SPEAKER_LEFT_X: int = 150  # PLACEHOLDER: x for left speaker on dual card
SPEAKER_RIGHT_X: int = 555  # PLACEHOLDER: x for right speaker on dual card
TEXT_AREA_Y_START: int = 870  # PLACEHOLDER: y where text block begins
FONT_SIZE_NAME: int = 48  # PLACEHOLDER
FONT_SIZE_TITLE: int = 36  # PLACEHOLDER
TEXT_SHADOW_COLOR: tuple[int, int, int] = (10, 20, 60)
TEXT_PRIMARY_COLOR: tuple[int, int, int] = (255, 255, 255)
TEXT_SAFE_WIDTH_RATIO: float = 0.85

CIRCLE_DIAMETER: int = 420
CIRCLE_BORDER_COLOR: tuple[int, int, int, int] = (80, 80, 80, 140)
CIRCLE_BORDER_WIDTH: int = 12


def remove_background(image_bytes: bytes, session: any) -> Image.Image:
    output_bytes = remove(image_bytes, session=session)
    return Image.open(BytesIO(output_bytes)).convert("RGBA")


def normalize_speaker_image(subject: Image.Image, target_height: int) -> Image.Image:
    bbox = subject.getbbox()
    if bbox:
        subject = subject.crop(bbox)

    width, height = subject.size
    aspect_ratio = width / height
    new_width = int(target_height * aspect_ratio)
    return subject.resize((new_width, target_height), Image.Resampling.LANCZOS)


def apply_circle_crop(image: Image.Image, diameter: int = CIRCLE_DIAMETER) -> Image.Image:
    image = image.convert("RGBA")
    src_w, src_h = image.size
    side = min(src_w, src_h)
    left = (src_w - side) // 2
    top = (src_h - side) // 2
    image = image.crop((left, top, left + side, top + side))
    image = image.resize((diameter, diameter), Image.Resampling.LANCZOS)

    mask = Image.new("L", (diameter, diameter), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, diameter - 1, diameter - 1), fill=255)

    result = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
    result.paste(image, (0, 0), mask)

    border_draw = ImageDraw.Draw(result, "RGBA")
    inset = CIRCLE_BORDER_WIDTH // 2
    border_draw.ellipse(
        (inset, inset, diameter - inset - 1, diameter - inset - 1),
        outline=CIRCLE_BORDER_COLOR,
        width=CIRCLE_BORDER_WIDTH,
    )

    return result


def composite_card(card: SessionCard, session: any, remove_bg: bool = True) -> Image.Image:
    # 1. Open template as RGBA
    if not TEMPLATE_PATH.exists():
        # Fallback for testing if template is missing
        canvas = Image.new("RGBA", (1080, 1350), (200, 200, 200, 255))
    else:
        canvas = Image.open(TEMPLATE_PATH).convert("RGBA")

    canvas_width, _ = canvas.size

    # 2. Process speakers
    processed_speakers = []
    for speaker in card.speakers:
        try:
            resp = requests.get(speaker.profile_picture_url, timeout=15)
            resp.raise_for_status()
            logger.debug(
                "Downloaded speaker image for %s (%d bytes)",
                speaker.full_name,
                len(resp.content),
            )

            if remove_bg:
                subject = remove_background(resp.content, session)
                subject = normalize_speaker_image(subject, SPEAKER_TARGET_HEIGHT)
            else:
                subject = Image.open(BytesIO(resp.content)).convert("RGBA")
                subject = apply_circle_crop(subject)
            processed_speakers.append(subject)
        except Exception:
            logger.error(f"Error processing speaker {speaker.full_name}", exc_info=True)
            # Skip this speaker

    # 3. Paste speakers
    num_speakers = len(processed_speakers)
    if num_speakers == 1:
        subject = processed_speakers[0]
        # Align bottom to SPEAKER_ANCHOR_Y
        paste_y = SPEAKER_ANCHOR_Y - SPEAKER_TARGET_HEIGHT
        canvas.paste(subject, (SPEAKER_SINGLE_X, paste_y), subject)
    elif num_speakers >= 2:
        # Dual speaker layout (taking first 2)
        # Left speaker
        subject_l = processed_speakers[0]
        paste_y_l = SPEAKER_ANCHOR_Y - SPEAKER_TARGET_HEIGHT
        canvas.paste(subject_l, (SPEAKER_LEFT_X, paste_y_l), subject_l)

        # Right speaker
        subject_r = processed_speakers[1]
        paste_y_r = SPEAKER_ANCHOR_Y - SPEAKER_TARGET_HEIGHT
        canvas.paste(subject_r, (SPEAKER_RIGHT_X, paste_y_r), subject_r)

    # 4. Render text
    draw = ImageDraw.Draw(canvas)
    _render_text_block(draw, card, canvas_width)

    return canvas.convert("RGB")


def _render_text_block(draw: ImageDraw.ImageDraw, card: SessionCard, canvas_width: int) -> None:
    try:
        font_name = ImageFont.truetype(str(FONT_PATH), FONT_SIZE_NAME)
        font_title = ImageFont.truetype(str(FONT_PATH), FONT_SIZE_TITLE)
    except Exception:
        logger.warning(
            "Custom font not found at %s — falling back to default", FONT_PATH, exc_info=True
        )
        font_name = ImageFont.load_default()
        font_title = ImageFont.load_default()

    # Speaker names
    names_text = " & ".join([s.full_name for s in card.speakers[:2]])

    # Horizontal centering for names
    name_bbox = draw.textbbox((0, 0), names_text, font=font_name)
    name_w = name_bbox[2] - name_bbox[0]
    name_x = (canvas_width - name_w) // 2

    # Render name with shadow
    draw.text(
        (name_x + 2, TEXT_AREA_Y_START + 2), names_text, font=font_name, fill=TEXT_SHADOW_COLOR
    )
    draw.text((name_x, TEXT_AREA_Y_START), names_text, font=font_name, fill=TEXT_PRIMARY_COLOR)

    # Talk title wrapping
    max_w = int(canvas_width * TEXT_SAFE_WIDTH_RATIO)
    lines = _wrap_text(card.talk_title, font_title, max_w, draw)

    current_y = TEXT_AREA_Y_START + FONT_SIZE_NAME + 20
    for line in lines:
        line_bbox = draw.textbbox((0, 0), line, font=font_title)
        line_w = line_bbox[2] - line_bbox[0]
        line_x = (canvas_width - line_w) // 2

        # Render line with shadow
        draw.text((line_x + 2, current_y + 2), line, font=font_title, fill=TEXT_SHADOW_COLOR)
        draw.text((line_x, current_y), line, font=font_title, fill=TEXT_PRIMARY_COLOR)

        current_y += (line_bbox[3] - line_bbox[1]) + 10


def _wrap_text(
    text: str, font: ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw
) -> list[str]:
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def composite_sponsor_card(sponsor: Sponsor) -> Image.Image | None:
    if not TEMPLATE_PATH.exists():
        canvas = Image.new("RGBA", (1080, 1350), (200, 200, 200, 255))
    else:
        canvas = Image.open(TEMPLATE_PATH).convert("RGBA")

    canvas_width, _ = canvas.size

    # Download image
    try:
        resp = requests.get(sponsor.logo_url, timeout=10)
        resp.raise_for_status()
        content = resp.content

        from io import BytesIO

        # Robust SVG detection: check first 8KB for b"<svg" case-insensitively
        content_prefix = content[:8192].lower()
        is_svg = sponsor.logo_url.lower().endswith(".svg") or b"<svg" in content_prefix

        if is_svg:
            # Safer decoding: try utf-8, fallback to latin-1
            try:
                svg_text = content.decode("utf-8")
            except UnicodeDecodeError:
                logger.warning(
                    f"SVG for {sponsor.name} is not valid UTF-8, falling back to latin-1"
                )
                svg_text = content.decode("latin-1")

            png_data = resvg_py.svg_to_bytes(svg_text)
            subject = Image.open(BytesIO(png_data)).convert("RGBA")
        else:
            subject = Image.open(BytesIO(content)).convert("RGBA")

        # Optimized single-pass resize for sponsors
        max_logo_width = int(canvas_width * 0.75)
        src_w, src_h = subject.size
        scale = min(max_logo_width / src_w, SPEAKER_TARGET_HEIGHT / src_h)

        # Resize once with the calculated scale
        new_w = int(src_w * scale)
        new_h = int(src_h * scale)
        subject = subject.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Draw sponsor logo centered (acting as single speaker)
        paste_y = SPEAKER_ANCHOR_Y - subject.size[1]

        # we center based on canvas width vs subject width
        logo_x = (canvas_width - subject.size[0]) // 2

        canvas.paste(subject, (logo_x, paste_y), subject)

    except Exception:
        logger.error(f"Error processing sponsor image for {sponsor.name}", exc_info=True)
        return None

    draw = ImageDraw.Draw(canvas)
    try:
        font_name = ImageFont.truetype(str(FONT_PATH), FONT_SIZE_NAME)
        font_title = ImageFont.truetype(str(FONT_PATH), FONT_SIZE_TITLE)
    except Exception:
        font_name = ImageFont.load_default()
        font_title = ImageFont.load_default()

    # Sponsor category (taking the title's place)
    max_text_w = int(canvas_width * TEXT_SAFE_WIDTH_RATIO)
    lines = _wrap_text(sponsor.category, font_title, max_text_w, draw)
    current_y = TEXT_AREA_Y_START + FONT_SIZE_NAME + 20
    for line in lines:
        line_bbox = draw.textbbox((0, 0), line, font=font_title)
        line_w = line_bbox[2] - line_bbox[0]
        line_x = (canvas_width - line_w) // 2
        draw.text((line_x + 2, current_y + 2), line, font=font_title, fill=TEXT_SHADOW_COLOR)
        draw.text((line_x, current_y), line, font=font_title, fill=TEXT_PRIMARY_COLOR)
        current_y += (line_bbox[3] - line_bbox[1]) + 10

    # Sponsor name (taking the name's place)
    name_bbox = draw.textbbox((0, 0), sponsor.name, font=font_name)
    name_w = name_bbox[2] - name_bbox[0]
    name_x = (canvas_width - name_w) // 2

    shadow_pos = (name_x + 2, TEXT_AREA_Y_START + 2)
    draw.text(shadow_pos, sponsor.name, font=font_name, fill=TEXT_SHADOW_COLOR)
    draw.text((name_x, TEXT_AREA_Y_START), sponsor.name, font=font_name, fill=TEXT_PRIMARY_COLOR)

    return canvas.convert("RGB")
