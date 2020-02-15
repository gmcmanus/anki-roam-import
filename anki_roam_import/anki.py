from typing import Iterable

from .model import JsonData, AnkiNote
from .roam import extract_roam_notes
from .translate import translate_note


def make_anki_notes(roam_pages: Iterable[JsonData]) -> Iterable[AnkiNote]:
    roam_notes = extract_roam_notes(roam_pages)
    return map(translate_note, roam_notes)
