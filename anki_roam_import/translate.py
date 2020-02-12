import re
from itertools import count
from typing import Callable

from .model import RoamNote, AnkiNote
from .roam import CLOZE_PATTERN


class NoteTranslator:
    def __init__(self, cloze_translator_factory: Callable[[], 'ClozeTranslator']):
        self.cloze_translator_factory = cloze_translator_factory

    def translate_note(self, roam_note: RoamNote) -> AnkiNote:
        return translate_note(roam_note, self.cloze_translator_factory())


def translate_note(roam_note: RoamNote, cloze_translator: 'ClozeTranslator') -> AnkiNote:
    return CLOZE_PATTERN.sub(cloze_translator, roam_note)


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
