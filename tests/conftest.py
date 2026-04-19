import pytest
from PIL import Image

from src.models import SessionCard, Speaker

SPEAKER_ONE_NAME = "Speaker One"
SPEAKER_ONE_PIC = "https://example.com/p1.jpg"


@pytest.fixture
def mock_sessionize_response():
    return {
        "sessions": [
            {
                "id": "s1",
                "title": "Single Speaker Talk",
                "isServiceSession": False,
                "isPlenumSession": False,
                "speakers": ["u1"],
                "categoryItems": [123],
            },
            {
                "id": "s2",
                "title": "Dual Speaker Talk",
                "isServiceSession": False,
                "isPlenumSession": False,
                "speakers": ["u1", "u2"],
            },
            {
                "id": "s3",
                "title": "Service Talk",
                "isServiceSession": True,
                "isPlenumSession": False,
                "speakers": ["u1"],
            },
            {
                "id": "s4",
                "title": "Plenum Talk",
                "isServiceSession": False,
                "isPlenumSession": True,
                "speakers": ["u1"],
            },
        ],
        "speakers": [
            {"id": "u1", "fullName": SPEAKER_ONE_NAME, "profilePicture": SPEAKER_ONE_PIC},
            {"id": "u2", "fullName": "Speaker Two", "profilePicture": "https://example.com/p2.jpg"},
        ],
        "categories": [{"title": "Track", "items": [{"id": 123, "name": "Testing Track"}]}],
    }


@pytest.fixture
def rgba_test_image():
    # 200x200 RGBA image with a 50x50 colored square centered on a transparent background
    img = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    for x in range(75, 125):
        for y in range(75, 125):
            img.putpixel((x, y), (255, 0, 0, 255))
    return img


@pytest.fixture
def dummy_card_single():
    s1 = Speaker(id="u1", full_name=SPEAKER_ONE_NAME, profile_picture_url=SPEAKER_ONE_PIC)
    return SessionCard(talk_title="Single Talk", speakers=(s1,), track="Testing Track")


@pytest.fixture
def dummy_card_dual():
    s1 = Speaker(id="u1", full_name=SPEAKER_ONE_NAME, profile_picture_url=SPEAKER_ONE_PIC)
    s2 = Speaker(id="u2", full_name="Speaker Two", profile_picture_url="https://example.com/p2.jpg")
    return SessionCard(talk_title="Dual Talk", speakers=(s1, s2))
