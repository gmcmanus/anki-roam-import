import datetime as dt
import json
import re
from dataclasses import dataclass
from typing import Iterable, List, Optional, TextIO
from zipfile import ZipFile, is_zipfile

from .model import JsonData, RoamNote


def load_roam_pages(path: str) -> Iterable[JsonData]:
    for file in generate_json_files(path):
        yield from json.load(file)


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

    def __call__(self, roam_pages: Iterable[JsonData]) -> Iterable[RoamNote]:
        for page in roam_pages:
            yield from self.extract_notes_from_children(page, [])

    def extract_notes_from_children(
        self,
        page_or_block: JsonData,
        parents: List[JsonData],
    ) -> Iterable[RoamNote]:

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


# TODO this captures KaTeX formulas too... e.g. $$\frac{a}{b}$$
# noinspection RegExpRedundantEscape
CLOZE_PATTERN = re.compile(
    r'''
        (?<! \{ )                      # don't match double bracket behind
        \{                             # opening bracket
        (?! \{ )                       # don't match double bracket ahead
        (?: c (?P<number> \d+ ) \| )?  # optional cloze number
        (?P<content> .+? )             # content
        (?: \| (?P<hint> .+? ) )?      # optional hint
        \}                             # closing bracket
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


@dataclass
class SourceFinder:
    source_extractor: 'SourceExtractor'

    def __call__(self, block: JsonData, parents: List[JsonData]) -> Optional[str]:
        source = self.find_source_in_children(block)

        if source is None:
            source = self.find_source_in_siblings_or_parents(block, parents)

        return source

    def find_source_in_children(self, block: JsonData) -> Optional[str]:
        if 'children' not in block:
            return None

        for child in block['children']:
            source = self.source_extractor(child)

            if source is not None:
                return source

    def find_source_in_siblings_or_parents(
        self, block: JsonData, parents: List[JsonData],
    ) -> Optional[str]:
        if not parents:
            return None

        source = self.find_source_in_siblings(block, parents[-1])

        if source is None:
            source = self.find_source_in_parents(parents)

        return source

    def find_source_in_siblings(
        self, block: JsonData, parent: JsonData,
    ) -> Optional[str]:
        after_block = False
        last_source_before_block = None

        for child in parent['children']:
            if child is block:
                after_block = True
                continue

            source = self.source_extractor(child)

            if source is None:
                continue

            if after_block:
                return source

            last_source_before_block = source

        return last_source_before_block

    def find_source_in_parents(self, parents: List[JsonData]) -> Optional[str]:
        for parent in reversed(parents):
            source = self.source_extractor(parent)

            if source is not None:
                return source

        return None


class SourceExtractor:
    def __call__(self, block: JsonData) -> Optional[str]:
        if 'string' not in block:
            return None

        string = block['string']
        match = SOURCE_PATTERN.search(string)

        if match:
            return match['source']

        return None


SOURCE_PATTERN = re.compile(
    r'''
        ^                  # start of string
        \s*                # leading whitespace
        source          
        (?: \s* : )+       # colons with intervening whitespace
        \s*                # leading whitespace
        (?P<source> .*? )  # source text
        \s*                # trailing whitespace
        $                  # end of string
    ''',
    flags=re.IGNORECASE | re.DOTALL | re.VERBOSE,
)


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
            formatted_source = f'{source}\n{formatted_source}'

        return formatted_source


@dataclass
class TimeFormatter:
    time_zone: Optional[dt.tzinfo]

    def __call__(self, timestamp_millis: int) -> str:
        timestamp_seconds = timestamp_millis / 1e3
        utc_datetime = dt.datetime.fromtimestamp(
            timestamp_seconds, dt.timezone.utc)
        local_zone_datetime = utc_datetime.astimezone(self.time_zone)
        return local_zone_datetime.isoformat(timespec='milliseconds')


extract_roam_notes = NoteExtractor(RoamNoteBuilder(SourceBuilder(
    SourceFinder(SourceExtractor()),
    SourceFormatter(TimeFormatter(time_zone=None)),
)))
