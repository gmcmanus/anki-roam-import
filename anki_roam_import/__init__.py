from typing import Iterable, Union, Dict, Any, List

# PyCharm doesn't infer well with:
# JsonData = Union[None, bool, str, float, int, List['JsonData'], Dict[str, 'JsonData']]
JsonData = Any
Note = str


def extract_notes(roam_json: JsonData) -> Iterable[Note]:
    for page in roam_json:
        yield from extract_notes_from_children(page)


def extract_notes_from_children(page_or_block: JsonData) -> Iterable[Note]:
    if 'children' not in page_or_block:
        return

    for block in page_or_block['children']:
        string = block['string']

        if contains_note(string):
            yield string

        yield from extract_notes_from_children(block)


def contains_note(string):
    return '{' in string and '}' in string


class NoteAdder:
    def add_note(self, note: Note) -> None:
        pass


def import_notes(notes: Iterable[Note], note_adder: NoteAdder) -> None:
    for note in notes:
        note_adder.add_note(note)
