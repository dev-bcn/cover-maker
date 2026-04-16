import io

from PIL import Image, ImageDraw

from src.image_processor import _wrap_text, normalize_speaker_image, remove_background


def test_normalize_crops_transparent_padding(rgba_test_image) -> None:
    # Original image is 200x200 with 50x50 subject at 75,75
    target_height = 100
    normalized = normalize_speaker_image(rgba_test_image, target_height)

    # Normalized height should be target_height
    assert normalized.height == target_height
    # Aspect ratio was 1:1, so width should be target_height
    assert normalized.width == target_height

    # Bounding box should now be the full image size (since it was cropped and resized)
    bbox = normalized.getbbox()
    assert bbox == (0, 0, target_height, target_height)


def test_wrap_text() -> None:
    # Use a dummy font and draw object
    img = Image.new("RGB", (1000, 100))
    draw = ImageDraw.Draw(img)

    # Since we can't easily mock font metrics, we'll check the logic with a small max_width
    text = "This is a long title that should wrap several times"
    # Mock font (default font roughly 6px wide per char)
    from PIL import ImageFont

    font = ImageFont.load_default()

    # Very small max_width to force wrap
    max_w = 50
    lines = _wrap_text(text, font, max_w, draw)

    assert len(lines) > 1
    assert " ".join(lines) == text


def test_remove_background(rgba_test_image) -> None:
    # Mock rembg.remove output
    buf = io.BytesIO()
    rgba_test_image.save(buf, format="PNG")
    mock_output_bytes = buf.getvalue()

    input_bytes = b"fake-input-bytes"

    # We need to mock rembg.remove
    import unittest.mock as mock

    with mock.patch("src.image_processor.remove", return_value=mock_output_bytes):
        # session can be None for mock
        result = remove_background(input_bytes, None)
        assert isinstance(result, Image.Image)
        assert result.mode == "RGBA"
        assert result.size == rgba_test_image.size


def test_composite_card_single(dummy_card_single, rgba_test_image) -> None:
    import unittest.mock as mock

    import src.image_processor

    # Mock download and background removal
    with mock.patch("requests.get") as mock_get:
        mock_get.return_value.content = b"fake-bytes"
        mock_get.return_value.raise_for_status = lambda: None

        with mock.patch("src.image_processor.remove_background", return_value=rgba_test_image):
            # No template files, so it uses fallback 1080x1350 canvas
            result = src.image_processor.composite_card(dummy_card_single, None)

            assert isinstance(result, Image.Image)
            assert result.size == (1080, 1350)
            assert result.mode == "RGB"


def test_composite_card_dual(dummy_card_dual, rgba_test_image) -> None:
    import unittest.mock as mock

    import src.image_processor

    with mock.patch("requests.get") as mock_get:
        mock_get.return_value.content = b"fake-bytes"
        mock_get.return_value.raise_for_status = lambda: None

        with mock.patch("src.image_processor.remove_background", return_value=rgba_test_image):
            result = src.image_processor.composite_card(dummy_card_dual, None)

            assert isinstance(result, Image.Image)
            assert result.size == (1080, 1350)
            # Should have called requests.get twice for 2 speakers
            assert mock_get.call_count == 2


def test_render_text_block_error_handling(dummy_card_single) -> None:
    from src.image_processor import _render_text_block

    img = Image.new("RGB", (1080, 1350))
    draw = ImageDraw.Draw(img)

    # Should not raise even if font path is invalid (it falls back to default)
    _render_text_block(draw, dummy_card_single, 1080)


def test_composite_sponsor_card(rgba_test_image) -> None:
    import unittest.mock as mock
    from src.models import Sponsor
    import src.image_processor

    sponsor = Sponsor(name="Test Sponsor", category="Test Category", image="http://test.com/logo.png")

    with mock.patch("requests.get") as mock_get:
        buf = io.BytesIO()
        rgba_test_image.save(buf, format="PNG")
        mock_get.return_value.content = buf.getvalue()
        mock_get.return_value.raise_for_status = lambda: None

        result = src.image_processor.composite_sponsor_card(sponsor)

        assert isinstance(result, Image.Image)
        assert result.size == (1080, 1350)
        assert result.mode == "RGB"
        assert mock_get.call_count == 1
