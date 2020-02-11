from typing import Iterable


class NoteAdder:
    def add_note(self, note: str) -> None:
        pass


def import_notes(notes: Iterable[str], note_adder: NoteAdder) -> None:
    for note in notes:
        note_adder.add_note(note)
