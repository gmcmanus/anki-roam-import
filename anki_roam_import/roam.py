import datetime as dt
import json
import re
from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional, TextIO
from zipfile import ZipFile, is_zipfile

from .model import (
    Cloze, ClozePart, CodeBlock, CodeInline, JsonData, Math, RoamBlock,
    RoamColonCommand, RoamCurlyCommand, RoamPart,
)
from .parser import (
    ParserGenerator, any_character, choose, delimited_text,
    exact_character_once_only, exact_string, full_parser, join_strings,
    nonnegative_integer, optional, parser_generator, peek, rest_of_string,
    start_of_string, zero_or_more,
)


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
class BlockExtractor:
    roam_block_builder: 'RoamBlockBuilder'

    def __call__(self, roam_pages: Iterable[JsonData]) -> Iterable[RoamBlock]:
        for page in roam_pages:
            yield from self.extract_blocks_from_children(page, [])

    def extract_blocks_from_children(
        self,
        page_or_block: JsonData,
        parents: List[JsonData],
    ) -> Iterable[RoamBlock]:

        if 'children' not in page_or_block:
            return

        parents.append(page_or_block)

        for block in page_or_block['children']:
            roam_block = self.roam_block_builder(block, parents)
            if roam_block:
                yield roam_block

            yield from self.extract_blocks_from_children(block, parents)

        parents.pop()


@dataclass
class RoamBlockBuilder:
    roam_parser: 'Callable[[str], List[RoamPart]]'
    source_builder: 'SourceBuilder'

    def __call__(
        self, block: JsonData, parents: List[JsonData],
    ) -> Optional[RoamBlock]:
        string = block['string']

        if not might_contain_cloze(string):
            return None

        parts = self.roam_parser(string)

        if not contains_cloze(parts):
            return None

        source = self.source_builder(block, parents)
        return RoamBlock(parts, source)


def might_contain_cloze(string: str) -> bool:
    return '{' in string and '}' in string


def contains_cloze(parts: List[RoamPart]) -> bool:
    return any(isinstance(part, Cloze) for part in parts)


@full_parser
@parser_generator
def parse_roam_block() -> ParserGenerator[List[RoamPart]]:
    roam_part = choose(
        roam_colon_command,
        roam_curly_command,
        cloze,
        math,
        code_block,
        code_inline,
        any_character,
    )
    roam_parts = yield zero_or_more(roam_part)
    return join_strings(roam_parts)


@parser_generator
def roam_colon_command() -> ParserGenerator[RoamCurlyCommand]:
    yield start_of_string
    yield exact_string(':')

    commands = 'diagram', 'hiccup', 'img', 'q'
    command = yield choose(*(exact_string(command) for command in commands))
    content = yield rest_of_string

    return RoamColonCommand(command, content)


@parser_generator
def roam_curly_command() -> ParserGenerator[RoamCurlyCommand]:
    # Roam currently parses differently, e.g.
    # {{{}} -> RoamCurlyCommand('{')
    # {{}}} -> RoamCurlyCommand('}')
    text = yield delimited_text('{{', '}}')
    return RoamCurlyCommand(text)


@parser_generator
def cloze() -> ParserGenerator[Cloze]:
    yield exact_character_once_only('{')
    number = yield optional(cloze_number)
    content = yield cloze_content
    hint = yield optional(cloze_hint)
    yield end_of_cloze

    return Cloze(content, hint, number)


@parser_generator
def end_of_cloze() -> ParserGenerator[str]:
    return (yield exact_character_once_only('}'))


@parser_generator
def start_of_hint() -> ParserGenerator[str]:
    return (yield exact_string('|'))


@parser_generator
def cloze_content() -> ParserGenerator[List[ClozePart]]:
    parts = []
    while True:
        if (yield peek(start_of_hint)) or (yield peek(end_of_cloze)):
            return join_strings(parts)

        part = yield choose(
            math,
            code_block,
            code_inline,
            any_character,
        )
        parts.append(part)


@parser_generator
def cloze_hint() -> ParserGenerator[str]:
    yield exact_string('|')

    characters = []
    while True:
        if (yield peek(end_of_cloze)):
            return ''.join(characters)

        character = yield any_character
        characters.append(character)


@parser_generator
def cloze_number() -> ParserGenerator[int]:
    yield exact_string('c')
    number = yield nonnegative_integer
    yield exact_string('|')
    return number


@parser_generator
def math() -> ParserGenerator[Math]:
    delimiter = '$$'
    text = yield delimited_text(delimiter, delimiter)
    return Math(text)


@parser_generator
def code_block() -> ParserGenerator[CodeBlock]:
    delimiter = '```'
    text = yield delimited_text(delimiter, delimiter)
    return CodeBlock(text)


@parser_generator
def code_inline() -> ParserGenerator[CodeInline]:
    delimiter = '`'
    text = yield delimited_text(delimiter, delimiter)
    return CodeInline(text)


@dataclass
class SourceBuilder:
    source_finder: 'SourceFinder'
    source_formatter: 'SourceFormatter'

    def __call__(self, block: JsonData, parents: List[JsonData]) -> str:
        source = self.source_finder(block, parents)
        page = parents[0]
        return self.source_formatter(block, source, page)


@dataclass
class SourceFinder:
    source_extractor: 'SourceExtractor'

    def __call__(
        self, block: JsonData, parents: List[JsonData],
    ) -> Optional[str]:
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

    def __call__(
        self, block: JsonData, source: Optional[str], page: JsonData,
    ) -> str:
        title = page['title']
        formatted_source = f"Note from Roam page '{title}'"

        if 'create-time' in block:
            create_time = self.time_formatter(block['create-time'])
            formatted_source += f', created at {create_time}'

        if 'edit-time' in block:
            edit_time = self.time_formatter(block['edit-time'])
            formatted_source += f', edited at {edit_time}'

        formatted_source += '.'

        if source is not None:
            formatted_source = f'{source}<br/>{formatted_source}'

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


extract_roam_blocks = BlockExtractor(RoamBlockBuilder(
    parse_roam_block,
    SourceBuilder(
        SourceFinder(SourceExtractor()),
        SourceFormatter(TimeFormatter(time_zone=None)),
    ),
))
