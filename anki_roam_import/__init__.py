import re
from typing import Iterable, Any, Callable

# PyCharm doesn't infer well with:
# JsonData = Union[None, bool, str, float, int, List['JsonData'], Dict[str, 'JsonData']]
JsonData = Any
RoamNote = str
AnkiNote = str


def extract_notes(roam_json: JsonData) -> Iterable[RoamNote]:
    for page in roam_json:
        yield from extract_notes_from_children(page)


def extract_notes_from_children(page_or_block: JsonData) -> Iterable[RoamNote]:
    if 'children' not in page_or_block:
        return

    for block in page_or_block['children']:
        string = block['string']

        if contains_note(string):
            yield string

        yield from extract_notes_from_children(block)


def contains_note(string: str) -> bool:
    return '{' in string and '}' in string


class AnkiDeck:
    def add_anki_note(self, note: AnkiNote) -> None:
        pass


class NoteAdder:
    def __init__(self, note_translator: Callable[[RoamNote], AnkiNote], deck: AnkiDeck):
        self.note_translator = note_translator
        self.deck = deck

    def add_roam_note(self, roam_note: RoamNote) -> None:
        anki_note = self.note_translator(roam_note)
        self.deck.add_anki_note(anki_note)


def translate_note(roam_note: RoamNote) -> AnkiNote:
    double_bracket_answer = r'\{\{' + answer_regex('double_bracket') + r'\}\}'
    single_bracket_answer = r'\{' + answer_regex('single_bracket') + r'\}'

    return re.sub(
        pattern=f'{double_bracket_answer}|{single_bracket_answer}',
        repl=ClozeTranslator(),
        string=roam_note,
        flags=re.DOTALL,
    )


def answer_regex(group_prefix):
    return f'(?:c(?P<{group_prefix}_cloze_number>\d+)::)?(?P<{group_prefix}_answer>.+?)'


def get_answer_group(match, group_suffix):
    value = match[f'double_bracket_{group_suffix}']
    if value is None:
        value = match[f'single_bracket_{group_suffix}']
    return value


class ClozeTranslator:
    def __init__(self):
        self.cloze_number = 0

    def __call__(self, match):
        cloze_number = get_answer_group(match, 'cloze_number')
        if cloze_number is not None:
            self.cloze_number = cloze_number
        else:
            self.cloze_number += 1

        answer = get_answer_group(match, 'answer')

        return '{{c' + str(self.cloze_number) + '::' + answer + '}}'


def import_roam_notes(notes: Iterable[RoamNote], note_adder: NoteAdder) -> None:
    for note in notes:
        note_adder.add_roam_note(note)
