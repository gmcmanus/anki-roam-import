import datetime as dt
import json
import re
from dataclasses import dataclass
from typing import Iterable, List, Optional, TextIO
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
                    with zip_file.open(name) as file:
                        yield file
    else:
        raise RuntimeError(f'Unknown file type: {path!r}')


def is_json_path(path: str) -> bool:
    return path.lower().endswith('.json')


@dataclass
class NoteExtractor:
    roam_note_builder: 'RoamNoteBuilder'

    def __call__(self, roam_json: JsonData) -> Iterable[RoamNote]:
        for page in roam_json:
            yield from self.extract_notes_from_children(page, [])

    def extract_notes_from_children(
            self, page_or_block: JsonData, parents: List[JsonData]) -> Iterable[RoamNote]:

        if 'children' not in page_or_block:
            return

        parents.append(page_or_block)

        for block in page_or_block['children']:
            roam_note = self.roam_note_builder(block, parents)
            if roam_note:
                yield roam_note

            yield from self.extract_notes_from_children(block, parents)

        parents.pop()


@dataclass
class RoamNoteBuilder:
    source_builder: 'SourceBuilder'

    def __call__(self, block: JsonData, parents: List[JsonData]) -> Optional[RoamNote]:
        string = block['string']

        if not contains_cloze(string):
            return None

        source = self.source_builder(block, parents)
        return RoamNote(string, source)


def contains_cloze(string: str) -> bool:
    return bool(CLOZE_PATTERN.search(string))


# noinspection RegExpRedundantEscape
CLOZE_PATTERN = re.compile(
    r'''
        (?<!\{)                 # don't match double bracket behind
        \{                      # opening bracket
        (?!\{)                  # don't match double bracket ahead
        (?:c(?P<number>\d+)\|)? # optional cloze number
        (?P<content>.+?)        # content
        (?:\|(?P<hint>.+?))?    # optional hint
        \}                      # closing bracket
    ''',
    flags=re.VERBOSE | re.DOTALL,
)


@dataclass
class SourceBuilder:
    source_finder: 'SourceFinder'
    source_formatter: 'SourceFormatter'

    def __call__(self, block: JsonData, parents: List[JsonData]) -> str:
        source = self.source_finder(block, parents)
        page = parents[0]
        return self.source_formatter(source, page)


class SourceFinder:
    def __call__(self, block: JsonData, parents: List[JsonData]) -> Optional[str]:
        pass


@dataclass
class SourceFormatter:
    time_formatter: 'TimeFormatter'

    def __call__(self, source: Optional[str], page: JsonData) -> str:
        title = page['title']
        formatted_source = f"Note from Roam page '{title}'"

        if 'create-time' in page:
            create_time = self.time_formatter(page['create-time'])
            formatted_source += f', created at {create_time}'

        if 'edit-time' in page:
            edit_time = self.time_formatter(page['edit-time'])
            formatted_source += f', edited at {edit_time}'

        formatted_source += '.'

        if source is not None:
            formatted_source = f'Source: {source}\n' + formatted_source

        return formatted_source


@dataclass
class TimeFormatter:
    time_zone: Optional[dt.tzinfo]

    def __call__(self, timestamp_millis: int) -> str:
        utc_datetime = dt.datetime.fromtimestamp(timestamp_millis / 1e3, dt.timezone.utc)
        local_zone_datetime = utc_datetime.astimezone(self.time_zone)
        return local_zone_datetime.isoformat(timespec='milliseconds')


extract_notes = NoteExtractor(RoamNoteBuilder(
    SourceBuilder(SourceFinder(), SourceFormatter(TimeFormatter(time_zone=None))),
))
