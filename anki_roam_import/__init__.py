from typing import Iterable, Union, Dict, Any, List

# PyCharm doesn't infer well with:
# JsonData = Union[None, bool, str, float, int, List['JsonData'], Dict[str, 'JsonData']]
JsonData = Any
Note = str


def extract_notes(roam_json: JsonData) -> Iterable[Note]:
    for page in roam_json:
        for block in page['children']:
            yield block['string']


class NoteAdder:
    def add_note(self, note: Note) -> None:
        pass


def import_notes(notes: Iterable[Note], note_adder: NoteAdder) -> None:
    for note in notes:
        note_adder.add_note(note)
