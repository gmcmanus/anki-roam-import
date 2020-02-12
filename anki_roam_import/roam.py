import json
import re
from typing import Iterable
from typing.io import TextIO
from zipfile import ZipFile, is_zipfile

from .model import JsonData, RoamNote


def extract_notes_from_path(path: str) -> Iterable[RoamNote]:
    for file in generate_json_files(path):
        json_data = json.load(file)
        yield from extract_notes(json_data)


def generate_json_files(path: str) -> Iterable[TextIO]:
    if is_json_path(path):
        with open(path, encoding='utf-8') as file:
            yield file
    elif is_zipfile(path):
        with ZipFile(path) as zip_file:
            for name in zip_file.namelist():
                if is_json_path(name):
                    with file.open(name) as file:
                        yield file
    else:
        raise RuntimeError(f'Unknown file type: {path!r}')


def is_json_path(path: str) -> bool:
    return path.lower().endswith('.json')


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
