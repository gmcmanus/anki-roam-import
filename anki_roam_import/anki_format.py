import html
from dataclasses import dataclass, replace
from typing import Any, Callable, Iterable, List, Optional, TypeVar

from .model import (
    AnkiNote, Cloze, ClozePart, CodeBlock, CodeInline, Math, RoamBlock,
    RoamColonCommand, RoamCurlyCommand, RoamPart,
)


OptionalFormatter = Callable[[Any], Optional[str]]
T = TypeVar('T')
Formatter = Callable[[T], str]


@dataclass
class AnkiNoteMaker:
    cloze_enumerator: 'ClozeEnumerator'
    roam_parts_formatter: Formatter[Iterable[RoamPart]]

    def __call__(self, roam_block: RoamBlock) -> AnkiNote:
        numbered_parts = self.cloze_enumerator(roam_block.parts)
        anki_content = self.roam_parts_formatter(numbered_parts)
        return AnkiNote(anki_content, roam_block.source)


class ClozeEnumerator:
    def __call__(self, parts: List[RoamPart]) -> Iterable[RoamPart]:
        used_numbers = {
            part.number
            for part in parts
            if isinstance(part, Cloze) and has_valid_number(part)
        }
        next_candidate_number = 1

        for part in parts:
            if isinstance(part, Cloze) and not has_valid_number(part):
                while next_candidate_number in used_numbers:
                    next_candidate_number += 1
                part = replace(part, number=next_candidate_number)
                used_numbers.add(next_candidate_number)

            yield part


def has_valid_number(cloze: Cloze) -> bool:
    return cloze.number and cloze.number > 0


def combine_formatters(*formatters: OptionalFormatter) -> Formatter:
    def combined_formatter(value: Any) -> str:
        for formatter in formatters:
            string = formatter(value)
            if string is not None:
                return string
        raise ValueError

    return combined_formatter


def roam_parts_formatter(
    roam_part_formatter: Formatter[RoamPart],
) -> Formatter[Iterable[RoamPart]]:
    def format_roam_parts(parts: Iterable[RoamPart]) -> str:
        return ''.join(map(roam_part_formatter, parts))

    return format_roam_parts


def cloze_formatter(
    cloze_part_formatter: Formatter[ClozePart],
) -> OptionalFormatter:
    def format_cloze(cloze: Any) -> Optional[str]:
        if not isinstance(cloze, Cloze):
            return None

        if not has_valid_number(cloze):
            raise ValueError

        if cloze.hint is not None:
            hint = f'::{cloze.hint}'
        else:
            hint = ''

        content = ''.join(map(cloze_part_formatter, cloze.parts))

        return '{{' + f'c{cloze.number}::{content}{hint}' + '}}'

    return format_cloze


def format_math(math: Any) -> Optional[str]:
    if not isinstance(math, Math):
        return None
    return rf'\({math.content}\)'


def code_block_formatter(code_formatter: Formatter[str]) -> OptionalFormatter:
    def format_code_block(code_block: Any) -> Optional[str]:
        if not isinstance(code_block, CodeBlock):
            return None
        inline_code = code_formatter(code_block.content)
        return f'<pre>{inline_code}</pre>'

    return format_code_block


def code_inline_formatter(code_formatter: Formatter[str]) -> OptionalFormatter:
    def format_code_inline(code_inline: Any) -> Optional[str]:
        if not isinstance(code_inline, CodeInline):
            return None
        return code_formatter(code_inline.content)

    return format_code_inline


def format_code(code: str) -> str:
    escaped_code = html.escape(code)
    return f'<code>{escaped_code}</code>'


def format_roam_curly_command(curly_command: Any) -> Optional[str]:
    if not isinstance(curly_command, RoamCurlyCommand):
        return None
    return '{{' + curly_command.content + '}}'


def format_roam_colon_command(colon_command: Any) -> Optional[str]:
    if not isinstance(colon_command, RoamColonCommand):
        return None
    return f':{colon_command.command}{colon_command.content}'


def format_string(string: Any) -> Optional[str]:
    if not isinstance(string, str):
        return None
    return string


def make_anki_note_maker():
    format_code_inline = code_inline_formatter(format_code)
    format_code_block = code_block_formatter(format_code)

    cloze_part_formatter = combine_formatters(
        format_string,
        format_math,
        format_code_block,
        format_code_inline,
    )

    roam_part_formatter = combine_formatters(
        format_string,
        cloze_formatter(cloze_part_formatter),
        format_math,
        format_code_block,
        format_code_inline,
        format_roam_curly_command,
        format_roam_colon_command,
    )

    return AnkiNoteMaker(
        ClozeEnumerator(), roam_parts_formatter(roam_part_formatter))


make_anki_note = make_anki_note_maker()
