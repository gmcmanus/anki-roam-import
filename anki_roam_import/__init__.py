from typing import Iterable, Union, Dict, Any, List


JsonData = Union[None, bool, str, float, int, List['JsonData'], Dict[str, 'JsonData']]
Note = str


def extract_notes(roam_json: JsonData) -> Iterable[Note]:
    yield from []


class NoteAdder:
    def add_note(self, note: Note) -> None:
        pass


def import_notes(notes: Iterable[Note], note_adder: NoteAdder) -> None:
    for note in notes:
        note_adder.add_note(note)
