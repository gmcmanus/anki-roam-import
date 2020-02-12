import re
from typing import Iterable

from .model import JsonData, RoamNote


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


def make_cloze_pattern() -> re.Pattern:
    double_bracket_answer = r'\{\{' + answer_regex('double_bracket') + r'\}\}'
    single_bracket_answer = r'\{' + answer_regex('single_bracket') + r'\}'
    return re.compile(f'{double_bracket_answer}|{single_bracket_answer}', flags=re.DOTALL)


def answer_regex(group_prefix: str) -> str:
    return fr'(?:c(?P<{group_prefix}_cloze_number>\d+)::)?(?P<{group_prefix}_answer>.+?)'


CLOZE_PATTERN = make_cloze_pattern()
