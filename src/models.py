from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Speaker:
    id: str
    full_name: str
    profile_picture_url: str


@dataclass(frozen=True)
class SessionCard:
    talk_title: str
    speakers: tuple[Speaker, ...]
    track: str | None = None


@dataclass(frozen=True)
class Sponsor:
    name: str
    category: Literal["Premium Sponsor", "Regular Sponsor", "Technical Sponsor"]
    logo_url: str
