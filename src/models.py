from dataclasses import dataclass


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
