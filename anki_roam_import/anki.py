from typing import Iterable

from .model import RoamNote, AnkiNote
from .translate import NoteTranslator


class AnkiDeck:
    def add_anki_note(self, note: AnkiNote) -> None:
        pass


class NoteAdder:
    def __init__(self, note_translator: 'NoteTranslator', deck: AnkiDeck):
        self.note_translator = note_translator
        self.deck = deck

    def add_roam_note(self, roam_note: RoamNote) -> None:
        anki_note = self.note_translator.translate_note(roam_note)
        self.deck.add_anki_note(anki_note)


def import_roam_notes(notes: Iterable[RoamNote], note_adder: NoteAdder) -> None:
    for note in notes:
        note_adder.add_roam_note(note)
