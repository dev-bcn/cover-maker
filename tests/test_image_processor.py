import io

from PIL import Image, ImageDraw

from src.image_processor import (
    _wrap_text,
    apply_circle_crop,
    normalize_speaker_image,
    remove_background,
)


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
    from pathlib import Path

    import src.image_processor

    with mock.patch.object(src.image_processor, "TEMPLATE_PATH", Path("/nonexistent/template.png")):
        with mock.patch("requests.get") as mock_get:
            buf = io.BytesIO()
            rgba_test_image.save(buf, format="PNG")
            mock_get.return_value.content = buf.getvalue()
            mock_get.return_value.raise_for_status = lambda: None

            with mock.patch("src.image_processor.remove_background", return_value=rgba_test_image):
                result = src.image_processor.composite_card(dummy_card_single, None)

                assert isinstance(result, Image.Image)
                assert result.size == (1080, 1350)
                assert result.mode == "RGB"


def test_composite_card_dual(dummy_card_dual, rgba_test_image) -> None:
    import unittest.mock as mock
    from pathlib import Path

    import src.image_processor

    with mock.patch.object(src.image_processor, "TEMPLATE_PATH", Path("/nonexistent/template.png")):
        with mock.patch("requests.get") as mock_get:
            buf = io.BytesIO()
            rgba_test_image.save(buf, format="PNG")
            mock_get.return_value.content = buf.getvalue()
            mock_get.return_value.raise_for_status = lambda: None

            with mock.patch("src.image_processor.remove_background", return_value=rgba_test_image):
                result = src.image_processor.composite_card(dummy_card_dual, None)

                assert isinstance(result, Image.Image)
                assert result.size == (1080, 1350)
                assert mock_get.call_count == 2


def test_render_text_block_error_handling(dummy_card_single) -> None:
    import unittest.mock as mock
    from pathlib import Path

    import src.image_processor
    from src.image_processor import _render_text_block

    with mock.patch.object(src.image_processor, "FONT_PATH", Path("/nonexistent/font.ttf")):
        img = Image.new("RGB", (1080, 1350))
        draw = ImageDraw.Draw(img)
        _render_text_block(draw, dummy_card_single, 1080)


def test_composite_sponsor_card(rgba_test_image) -> None:
    import unittest.mock as mock
    from pathlib import Path

    import src.image_processor
    from src.models import Sponsor

    sponsor = Sponsor(name="Test Sponsor", category="Test Category", logo_url="http://test.com/logo.png")

    with mock.patch.object(src.image_processor, "TEMPLATE_PATH", Path("/nonexistent/template.png")):
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


def test_apply_circle_crop_shape() -> None:
    source = Image.new("RGBA", (300, 200), (255, 0, 0, 255))
    diameter = 100
    result = apply_circle_crop(source, diameter)

    assert result.mode == "RGBA"
    assert result.size == (diameter, diameter)


def test_apply_circle_crop_corners_are_transparent() -> None:
    source = Image.new("RGBA", (200, 200), (255, 0, 0, 255))
    diameter = 100
    result = apply_circle_crop(source, diameter)

    assert result.getpixel((0, 0))[3] == 0
    assert result.getpixel((diameter - 1, 0))[3] == 0
    assert result.getpixel((0, diameter - 1))[3] == 0
    assert result.getpixel((diameter - 1, diameter - 1))[3] == 0


def test_apply_circle_crop_center_is_opaque() -> None:
    source = Image.new("RGBA", (200, 200), (255, 0, 0, 255))
    diameter = 100
    result = apply_circle_crop(source, diameter)
    cx, cy = diameter // 2, diameter // 2

    assert result.getpixel((cx, cy))[3] == 255


def test_composite_card_no_bg_uses_circle_crop(dummy_card_single, rgba_test_image) -> None:
    import unittest.mock as mock

    import src.image_processor

    with mock.patch("requests.get") as mock_get:
        buf = io.BytesIO()
        rgba_test_image.save(buf, format="PNG")
        mock_get.return_value.content = buf.getvalue()
        mock_get.return_value.raise_for_status = lambda: None

        with mock.patch(
            "src.image_processor.apply_circle_crop", wraps=src.image_processor.apply_circle_crop
        ) as mock_circle:
            src.image_processor.composite_card(dummy_card_single, None, remove_bg=False)
            mock_circle.assert_called_once()


def test_composite_card_skips_failed_speaker(dummy_card_single) -> None:
    import unittest.mock as mock

    import src.image_processor

    with mock.patch("requests.get", side_effect=Exception("network error")):
        result = src.image_processor.composite_card(dummy_card_single, None)
        assert isinstance(result, Image.Image)
        assert result.size == (1080, 1350)


def test_composite_sponsor_card_returns_none_on_request_failure() -> None:
    import unittest.mock as mock

    import src.image_processor
    from src.models import Sponsor

    sponsor = Sponsor(name="Fail Sponsor", category="Regular Sponsor", logo_url="http://test.com/logo.png")

    with mock.patch("requests.get", side_effect=Exception("request failed")):
        result = src.image_processor.composite_sponsor_card(sponsor)
        assert result is None


def test_composite_sponsor_card_svg(rgba_test_image) -> None:
    import io as _io
    import unittest.mock as mock

    import src.image_processor
    from src.models import Sponsor

    sponsor = Sponsor(name="SVG Sponsor", category="Premium Sponsor", logo_url="http://test.com/logo.svg")

    png_buf = _io.BytesIO()
    rgba_test_image.save(png_buf, format="PNG")
    png_bytes = png_buf.getvalue()

    with mock.patch("requests.get") as mock_get:
        mock_get.return_value.content = b"<svg></svg>"
        mock_get.return_value.raise_for_status = lambda: None

        with mock.patch("src.image_processor.resvg_py.svg_to_bytes", return_value=png_bytes):
            result = src.image_processor.composite_sponsor_card(sponsor)
            assert isinstance(result, Image.Image)
            assert result.size == (1080, 1350)


def test_composite_card_uses_template_when_present(
    dummy_card_single, rgba_test_image, tmp_path
) -> None:
    import unittest.mock as mock

    import src.image_processor

    template = Image.new("RGBA", (1080, 1350), (50, 50, 50, 255))
    template_path = tmp_path / "base_template.png"
    template.save(template_path)

    with mock.patch.object(src.image_processor, "TEMPLATE_PATH", template_path):
        with mock.patch("requests.get") as mock_get:
            buf = io.BytesIO()
            rgba_test_image.save(buf, format="PNG")
            mock_get.return_value.content = buf.getvalue()
            mock_get.return_value.raise_for_status = lambda: None

            with mock.patch("src.image_processor.remove_background", return_value=rgba_test_image):
                result = src.image_processor.composite_card(dummy_card_single, None)
                assert isinstance(result, Image.Image)
                assert result.size == (1080, 1350)


def test_composite_sponsor_card_uses_template_when_present(rgba_test_image, tmp_path) -> None:
    import unittest.mock as mock

    import src.image_processor
    from src.models import Sponsor

    template = Image.new("RGBA", (1080, 1350), (50, 50, 50, 255))
    template_path = tmp_path / "base_template.png"
    template.save(template_path)

    sponsor = Sponsor(name="Tpl Sponsor", category="Technical Sponsor", logo_url="http://test.com/logo.png")

    with mock.patch.object(src.image_processor, "TEMPLATE_PATH", template_path):
        with mock.patch("requests.get") as mock_get:
            buf = io.BytesIO()
            rgba_test_image.save(buf, format="PNG")
            mock_get.return_value.content = buf.getvalue()
            mock_get.return_value.raise_for_status = lambda: None

            result = src.image_processor.composite_sponsor_card(sponsor)
            assert isinstance(result, Image.Image)
            assert result.size == (1080, 1350)


def test_render_text_block_with_real_font(dummy_card_single, tmp_path) -> None:
    import unittest.mock as mock

    from PIL import ImageFont as _ImageFont

    import src.image_processor
    from src.image_processor import _render_text_block

    fake_font_path = tmp_path / "DejaVuSans.ttf"

    with mock.patch.object(src.image_processor, "FONT_PATH", fake_font_path):
        with mock.patch(
            "src.image_processor.ImageFont.truetype",
            return_value=_ImageFont.load_default(),
        ):
            img = Image.new("RGB", (1080, 1350))
            draw = ImageDraw.Draw(img)
            _render_text_block(draw, dummy_card_single, 1080)


