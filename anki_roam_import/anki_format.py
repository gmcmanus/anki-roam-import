import html
import re
from dataclasses import dataclass, replace
from typing import Any, Callable, Iterable, List, Match, Optional, TypeVar

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
    html_formatter: Formatter[str]

    def __call__(self, roam_block: RoamBlock) -> AnkiNote:
        numbered_parts = self.cloze_enumerator(roam_block.parts)
        anki_content = self.roam_parts_formatter(numbered_parts)
        source_html = self.html_formatter(roam_block.source)
        return AnkiNote(anki_content, source_html)


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
    cloze_part_formatter: Formatter[ClozePart], html_formatter: Formatter[str],
) -> OptionalFormatter:
    def format_cloze(cloze: Any) -> Optional[str]:
        if not isinstance(cloze, Cloze):
            return None

        if not has_valid_number(cloze):
            raise ValueError

        if cloze.hint is not None:
            hint_html = html_formatter(cloze.hint)
            hint = f'::{hint_html}'
        else:
            hint = ''

        content = ''.join(map(cloze_part_formatter, cloze.parts))

        return '{{' + f'c{cloze.number}::{content}{hint}' + '}}'

    return format_cloze


def format_text_as_html(text: str) -> str:
    escaped_html = html.escape(text)
    escaped_html = MULTIPLE_SPACES.sub(replace_spaces_with_nbsp, escaped_html)
    return escaped_html.replace('\n', '<br>')


MULTIPLE_SPACES = re.compile(' {2,}')


def replace_spaces_with_nbsp(match: Match):
    return '&nbsp;' * len(match.group())


def math_formatter(html_formatter: Formatter[str]) -> OptionalFormatter:
    def format_math(math: Any) -> Optional[str]:
        if not isinstance(math, Math):
            return None
        math_html = html_formatter(math.content)
        return rf'\({math_html}\)'

    return format_math


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


def roam_curly_command_formatter(
    html_formatter: Formatter[str],
) -> OptionalFormatter:
    def format_roam_curly_command(curly_command: Any) -> Optional[str]:
        if not isinstance(curly_command, RoamCurlyCommand):
            return None
        command_html = html_formatter(curly_command.content)
        return '{{' + command_html + '}}'

    return format_roam_curly_command


def roam_colon_command_formatter(
    html_formatter: Formatter[str],
) -> OptionalFormatter:
    def format_roam_colon_command(colon_command: Any) -> Optional[str]:
        if not isinstance(colon_command, RoamColonCommand):
            return None
        command_html = html_formatter(colon_command.command)
        content_html = html_formatter(colon_command.content)
        return f':{command_html}{content_html}'

    return format_roam_colon_command


def string_formatter(html_formatter: Formatter[str]) -> OptionalFormatter:
    def format_string(string: Any) -> Optional[str]:
        if not isinstance(string, str):
            return None
        return html_formatter(string)
    return format_string


def make_anki_note_maker():
    format_string = string_formatter(format_text_as_html)
    format_math = math_formatter(format_text_as_html)
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
        cloze_formatter(cloze_part_formatter, format_text_as_html),
        format_math,
        format_code_block,
        format_code_inline,
        roam_curly_command_formatter(format_text_as_html),
        roam_colon_command_formatter(format_text_as_html),
    )

    return AnkiNoteMaker(
        ClozeEnumerator(),
        roam_parts_formatter(roam_part_formatter),
        format_text_as_html,
    )


make_anki_note = make_anki_note_maker()
