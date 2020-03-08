from dataclasses import replace
from typing import Any, Iterable, Optional

import pytest

from anki_roam_import.anki_format import (
    AnkiNoteMaker, ClozeEnumerator, Formatter, cloze_formatter,
    code_block_formatter, code_inline_formatter, combine_formatters,
    format_code, format_text_as_html, math_formatter,
    roam_colon_command_formatter, roam_curly_command_formatter,
    string_formatter,
)
from anki_roam_import.model import (
    AnkiNote, Cloze, ClozePart, CodeBlock, CodeInline, Math, RoamBlock,
    RoamColonCommand, RoamCurlyCommand, RoamPart,
)

from tests.util import mock, when


def test_make_note(mock_html_formatter):
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

    when(mock_html_formatter).called_with('source').then_return('html source')

    note_maker = AnkiNoteMaker(
        cloze_enumerator, roam_parts_formatter, mock_html_formatter,
    )

    assert note_maker(roam_block) == AnkiNote(formatted_note, 'html source')


def test_use_first_formatter_that_returns_string():
    # noinspection PyUnusedLocal
    def first_formatter(value: Any) -> Optional[str]:
        return None

    # noinspection PyUnusedLocal
    def second_formatter(value: Any) -> Optional[str]:
        return 'formatted string'

    formatter = combine_formatters(first_formatter, second_formatter)

    assert formatter('string') == 'formatted string'


def test_raise_value_error_if_no_formatter_matches():
    # noinspection PyUnusedLocal
    def none_formatter(value: Any) -> Optional[str]:
        return None

    formatter = combine_formatters(none_formatter)

    with pytest.raises(ValueError):
        formatter('string')


@pytest.fixture
def format_cloze(
    mock_cloze_part_formatter, mock_html_formatter,
) -> Formatter[Cloze]:
    return cloze_formatter(mock_cloze_part_formatter, mock_html_formatter)


@pytest.fixture
def mock_cloze_part_formatter() -> Formatter[ClozePart]:
    return mock(Formatter[ClozePart])


@pytest.fixture
def mock_html_formatter() -> Formatter[str]:
    return mock(Formatter[str])


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
    format_cloze, mock_cloze_part_formatter, mock_html_formatter,
):
    cloze = Cloze(['part'], 'hint', number=1)
    (when(mock_cloze_part_formatter)
     .called_with('part')
     .then_return('formatted part'))
    (when(mock_html_formatter)
     .called_with('hint')
     .then_return('html hint'))

    assert format_cloze(cloze) == '{{c1::formatted part::html hint}}'


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


def test_format_text_as_html_returns_equal_string_without_html():
    assert format_text_as_html('string') == 'string'


def test_format_text_as_html_escapes_html_elements():
    assert format_text_as_html('<&>') == '&lt;&amp;&gt;'


def test_format_text_as_html_leaves_single_spaces_as_spaces():
    assert format_text_as_html('a b') == 'a b'


def test_format_text_as_html_converts_consecutive_spaces_to_nbsp():
    assert format_text_as_html('a  b') == 'a&nbsp;&nbsp;b'


def test_format_text_as_html_converts_newline_to_br():
    assert format_text_as_html('a\nb') == 'a<br/>b'


@pytest.fixture
def format_string(mock_html_formatter):
    return string_formatter(mock_html_formatter)


def test_format_string_returns_html_formatted_string(
    format_string, mock_html_formatter,
):
    when(mock_html_formatter).called_with('string').then_return('html string')
    assert format_string('string') == 'html string'


def test_format_string_returns_none_if_not_given_string(format_string):
    assert format_string(0) is None


@pytest.fixture
def format_math(mock_html_formatter):
    return math_formatter(mock_html_formatter)


def test_format_math_formats_math_object(format_math, mock_html_formatter):
    when(mock_html_formatter).called_with('math').then_return('html math')
    assert format_math(Math('math')) == r'\(html math\)'


def test_format_math_returns_none_if_not_given_math_object(format_math):
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


def test_format_code_escapes_html_elements():
    formatted_code = format_code('<content&>')
    assert formatted_code == '<code>&lt;content&amp;&gt;</code>'


def test_format_code_preserves_whitespace():
    formatted_code = format_code('  \n  ')
    assert formatted_code == '<code>  \n  </code>'


@pytest.fixture
def format_roam_curly_command(mock_html_formatter):
    return roam_curly_command_formatter(mock_html_formatter)


def test_format_roam_curly_command(
    format_roam_curly_command, mock_html_formatter,
):
    command = RoamCurlyCommand('command')
    when(mock_html_formatter).called_with('command').then_return('html command')
    assert format_roam_curly_command(command) == '{{html command}}'


def test_format_roam_curly_command_returns_none_when_not_given_curly_command(
    format_roam_curly_command,
):
    assert format_roam_curly_command('') is None


@pytest.fixture
def format_roam_colon_command(mock_html_formatter):
    return roam_colon_command_formatter(mock_html_formatter)


def test_format_roam_colon_command(
    format_roam_colon_command, mock_html_formatter,
):
    when(mock_html_formatter).called_with('command').then_return('html command')
    when(mock_html_formatter).called_with('content').then_return('html content')
    command = RoamColonCommand('command', 'content')

    assert format_roam_colon_command(command) == ':html commandhtml content'


def test_format_roam_colon_command_returns_none_when_not_given_colon_command(
   format_roam_colon_command,
):
    assert format_roam_colon_command('') is None
