from anki_roam_import.model import (
    Cloze, CodeBlock, CodeInline, Math, RoamColonCommand, RoamCurlyCommand,
)
from anki_roam_import.roam import parse_roam_block


def test_parse_string():
    assert parse_roam_block('text') == ['text']


def test_parse_cloze():
    assert parse_roam_block('{cloze}') == [Cloze(['cloze'])]


def test_simple_note_with_double_brackets():
    assert parse_roam_block('{{content}}') == [RoamCurlyCommand('content')]


def test_simple_note_with_malformed_double_brackets():
    assert parse_roam_block('{ {content}}') == ['{ {content}}']


def test_simple_note_with_single_brackets_inside_double_brackets():
    text = ' query: {and: [[TODO]]} '
    assert parse_roam_block('{{' + text + '}}') == [RoamCurlyCommand(text)]


def test_colon_command_with_curly_brackets():
    assert parse_roam_block(':hiccup {text}') == [
        RoamColonCommand('hiccup', ' {text}')]


def test_colon_command_with_space_before():
    text = ' :hiccup text'
    assert parse_roam_block(text) == [text]


def test_colon_command_with_space_after():
    text = ': hiccup text'
    assert parse_roam_block(text) == [text]


def test_colon_command_with_non_whitespace_text_immediately_after():
    assert parse_roam_block(':hiccuptext') == [
        RoamColonCommand('hiccup', 'text')]


def test_code_inline():
    assert parse_roam_block('`{code}`') == [CodeInline('{code}')]


def test_code_block():
    assert parse_roam_block('```{code}```') == [CodeBlock('{code}')]


def test_simple_note_with_newline():
    assert parse_roam_block('{con\ntent}') == [Cloze(['con\ntent'])]


def test_simple_note_with_hint():
    assert parse_roam_block('{content|hint}') == [Cloze(['content'], 'hint')]


def test_note_with_cloze_number():
    assert parse_roam_block('{c0|content}') == [Cloze(['content'], number=0)]


def test_note_with_cloze_number_and_hint():
    assert parse_roam_block('{c0|content|hint}') == [
        Cloze(['content'], 'hint', number=0)]


def test_note_with_cloze_then_text():
    assert parse_roam_block('{c1|content} text') == [
        Cloze(['content'], number=1), ' text']


def test_note_with_text_then_cloze():
    assert parse_roam_block('text{c1|content}') == [
        'text', Cloze(['content'], number=1)]


def test_parse_math_part():
    assert parse_roam_block(r'$$\textrm{math}$$') == [Math(r'\textrm{math}')]


def test_parse_cloze_containing_math():
    parts = parse_roam_block(r'{$$\textrm{math}$$}')
    assert parts == [Cloze([Math(r'\textrm{math}')])]


def test_parse_cloze_containing_code_inline():
    parts = parse_roam_block('{`code``code`}')
    assert parts == [Cloze([CodeInline('code'), CodeInline('code')])]


def test_parse_cloze_containing_code_block():
    parts = parse_roam_block('{```co``de```}')
    assert parts == [Cloze([CodeBlock('co``de')])]
