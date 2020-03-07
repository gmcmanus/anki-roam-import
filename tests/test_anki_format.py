from dataclasses import replace
from typing import Any, Iterable, Optional

import pytest

from anki_roam_import.anki_format import (
    AnkiNoteMaker, ClozeEnumerator, Formatter, cloze_formatter,
    code_block_formatter, code_inline_formatter,
    combine_formatters, format_code, format_math, format_roam_colon_command,
    format_roam_curly_command, format_string,
)
from anki_roam_import.model import (
    AnkiNote, Cloze, ClozePart, CodeBlock, CodeInline, Math, RoamBlock,
    RoamColonCommand, RoamCurlyCommand, RoamPart,
)

from tests.util import mock, when


def test_make_note():
    cloze = Cloze(['content'])
    roam_block = RoamBlock([cloze], 'source')

    cloze_enumerator = mock(ClozeEnumerator)
    numbered_cloze = replace(cloze, number=1)
    when(cloze_enumerator).called_with([cloze]).then_return([numbered_cloze])

    roam_parts_formatter = mock(Formatter[Iterable[RoamPart]])
    formatted_note = '{{c1::content}}'
    (when(roam_parts_formatter)
     .called_with([numbered_cloze])
     .then_return(formatted_note))

    note_maker = AnkiNoteMaker(cloze_enumerator, roam_parts_formatter)

    assert note_maker(roam_block) == AnkiNote(formatted_note, 'source')


def test_use_first_formatter_that_returns_string():
    def first_formatter(value: Any) -> Optional[str]:
        return None

    def second_formatter(value: Any) -> Optional[str]:
        return 'formatted string'

    formatter = combine_formatters(first_formatter, second_formatter)

    assert formatter('string') == 'formatted string'


def test_raise_value_error_if_no_formatter_matches():
    def none_formatter(value: Any) -> Optional[str]:
        return None

    formatter = combine_formatters(none_formatter)

    with pytest.raises(ValueError):
        formatter('string')


@pytest.fixture
def format_cloze(mock_cloze_part_formatter) -> Formatter[Cloze]:
    return cloze_formatter(mock_cloze_part_formatter)


@pytest.fixture
def mock_cloze_part_formatter() -> Formatter[ClozePart]:
    return mock(Formatter[ClozePart])


def test_cloze_formatter_joins_cloze_parts(
    format_cloze, mock_cloze_part_formatter,
):
    (when(mock_cloze_part_formatter)
     .called_with('part 1')
     .then_return('formatted part 1'))
    (when(mock_cloze_part_formatter)
     .called_with('part 2')
     .then_return('formatted part 2'))
    cloze = Cloze(['part 1', 'part 2'], number=1)

    formatted_cloze = format_cloze(cloze)

    assert formatted_cloze == '{{c1::formatted part 1formatted part 2}}'


def test_cloze_formatter_formats_cloze_number(
    format_cloze, mock_cloze_part_formatter,
):
    cloze = Cloze(['part'], number=2)
    (when(mock_cloze_part_formatter)
     .called_with('part')
     .then_return('formatted part'))

    formatted_cloze = format_cloze(cloze)
    assert formatted_cloze == '{{c2::formatted part}}'


def test_cloze_formatter_formats_hint(
    format_cloze, mock_cloze_part_formatter,
):
    cloze = Cloze(['part'], 'hint', number=1)
    (when(mock_cloze_part_formatter)
     .called_with('part')
     .then_return('formatted part'))

    assert format_cloze(cloze) == '{{c1::formatted part::hint}}'


def test_cloze_formatter_raises_value_error_on_unnumbered_cloze(format_cloze):
    with pytest.raises(ValueError):
        format_cloze(Cloze(['part']))


def test_cloze_formatter_returns_none_if_not_given_cloze(format_cloze):
    assert format_cloze('') is None


def test_cloze_formatter_raises_value_error_on_zero_numbered_cloze(
    format_cloze,
):
    with pytest.raises(ValueError):
        format_cloze(Cloze(['part'], number=0))


def test_format_string_returns_equal_string():
    assert format_string('string') == 'string'


def test_format_string_returns_none_if_not_given_string():
    assert format_string(0) is None


def test_format_math_formats_math_object():
    assert format_math(Math('content')) == r'\(content\)'


def test_format_math_returns_none_if_not_given_math_object():
    assert format_math('') is None


def test_code_block_formatter():
    code_formatter = mock(Formatter[str])
    when(code_formatter).called_with('code').then_return('<code>code</code>')
    format_code_block = code_block_formatter(code_formatter)

    formatted_code = format_code_block(CodeBlock('code'))

    assert formatted_code == '<pre><code>code</code></pre>'


def test_code_block_formatter_returns_none_if_not_given_code_block_object():
    code_formatter = mock(Formatter[str])
    format_code_block = code_block_formatter(code_formatter)

    assert format_code_block('') is None


def test_code_inline_formatter():
    code_formatter = mock(Formatter[str])
    when(code_formatter).called_with('code').then_return('<code>code</code>')
    format_code_inline = code_inline_formatter(code_formatter)

    formatted_code = format_code_inline(CodeInline('code'))

    assert formatted_code == '<code>code</code>'


def test_code_inline_formatter_returns_none_when_not_given_code_inline():
    code_formatter = mock(Formatter[str])
    format_code_inline = code_inline_formatter(code_formatter)

    assert format_code_inline('') is None


def test_format_code():
    formatted_code = format_code('<content&>')
    assert formatted_code == '<code>&lt;content&amp;&gt;</code>'


def test_format_roam_curly_command():
    command = RoamCurlyCommand('content')
    assert format_roam_curly_command(command) == '{{content}}'


def test_format_roam_curly_command_returns_none_when_not_given_curly_command():
    assert format_roam_curly_command('') is None


def test_format_roam_colon_command():
    command = RoamColonCommand('command', 'content')
    assert format_roam_colon_command(command) == ':commandcontent'


def test_format_roam_colon_command_returns_none_when_not_given_colon_command():
    assert format_roam_colon_command('') is None
