from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont
from rembg import remove

from models import SessionCard

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


def remove_background(image_bytes: bytes, session: any) -> Image.Image:
    output_bytes = remove(image_bytes, session=session)
    from io import BytesIO

    return Image.open(BytesIO(output_bytes)).convert("RGBA")


def normalize_speaker_image(subject: Image.Image, target_height: int) -> Image.Image:
    # Crop to the bounding box of non-transparent pixels
    bbox = subject.getbbox()
    if bbox:
        subject = subject.crop(bbox)

    # Resize proportionally to target_height
    width, height = subject.size
    aspect_ratio = width / height
    new_width = int(target_height * aspect_ratio)
    return subject.resize((new_width, target_height), Image.Resampling.LANCZOS)


def composite_card(card: SessionCard, session: any) -> Image.Image:
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
            resp = requests.get(speaker.profile_picture_url)
            resp.raise_for_status()
            subject = remove_background(resp.content, session)
            subject = normalize_speaker_image(subject, SPEAKER_TARGET_HEIGHT)
            processed_speakers.append(subject)
        except Exception as e:
            print(f"Error processing speaker {speaker.full_name}: {e}")
            # Continue with other speakers or skip

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
        # Fallback to default font if custom font is missing
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
