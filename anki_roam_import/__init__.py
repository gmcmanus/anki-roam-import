import re
from typing import Iterable, Any, Callable
from itertools import count


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

        if contains_cloze(string):
            yield string

        yield from extract_notes_from_children(block)


def contains_cloze(string: str) -> bool:
    return bool(CLOZE_PATTERN.search(string))


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


class NoteTranslator:
    def __init__(self, cloze_translator_factory: Callable[[], 'ClozeTranslator']):
        self.cloze_translator_factory = cloze_translator_factory

    def translate_note(self, roam_note: RoamNote) -> AnkiNote:
        return translate_note(roam_note, self.cloze_translator_factory())


def translate_note(roam_note: RoamNote, cloze_translator: 'ClozeTranslator') -> AnkiNote:
    return CLOZE_PATTERN.sub(cloze_translator, roam_note)


def make_cloze_pattern() -> re.Pattern:
    double_bracket_answer = r'\{\{' + answer_regex('double_bracket') + r'\}\}'
    single_bracket_answer = r'\{' + answer_regex('single_bracket') + r'\}'
    return re.compile(f'{double_bracket_answer}|{single_bracket_answer}', flags=re.DOTALL)


def answer_regex(group_prefix: str) -> str:
    return fr'(?:c(?P<{group_prefix}_cloze_number>\d+)::)?(?P<{group_prefix}_answer>.+?)'


CLOZE_PATTERN = make_cloze_pattern()


class ClozeTranslator:
    def __init__(self):
        self.min_unused_cloze_number = 1
        self.used_cloze_numbers = set()

    def __call__(self, match: re.Match) -> str:
        cloze_number = get_answer_group(match, 'cloze_number')
        if cloze_number is not None:
            cloze_number = int(cloze_number)
        else:
            cloze_number = self._next_unused_cloze_number()

        self.used_cloze_numbers.add(cloze_number)
        answer = get_answer_group(match, 'answer')

        return '{{c' + str(cloze_number) + '::' + answer + '}}'

    def _next_unused_cloze_number(self) -> int:
        for cloze_number in count(self.min_unused_cloze_number):
            if cloze_number not in self.used_cloze_numbers:
                self.min_unused_cloze_number = cloze_number
                return cloze_number


def get_answer_group(match: re.Match, group_suffix: str) -> str:
    value = match[f'double_bracket_{group_suffix}']
    if value is None:
        value = match[f'single_bracket_{group_suffix}']
    return value


def import_roam_notes(notes: Iterable[RoamNote], note_adder: NoteAdder) -> None:
    for note in notes:
        note_adder.add_roam_note(note)
