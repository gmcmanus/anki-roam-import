import pytest

from anki_roam_import.translate import ClozeSplitter, Cloze


@pytest.fixture
def cloze_splitter():
    return ClozeSplitter()


def test_simple_note(cloze_splitter):
    assert list(cloze_splitter('{content}')) == [Cloze(content='content')]


def test_simple_note_with_double_brackets(cloze_splitter):
    assert list(cloze_splitter('{{content}}')) == ['{{content}}']


def test_simple_note_with_newline(cloze_splitter):
    assert list(cloze_splitter('{con\ntent}')) == [Cloze(content='con\ntent')]


def test_simple_note_with_hint(cloze_splitter):
    assert list(cloze_splitter('{content|hint}')) == [Cloze(content='content', hint='hint')]


def test_note_with_cloze_number(cloze_splitter):
    assert list(cloze_splitter('{c0|content}')) == [Cloze(content='content', number=0)]


def test_note_with_cloze_number_and_hint(cloze_splitter):
    assert list(cloze_splitter('{c0|content|hint}')) == [Cloze(content='content', hint='hint', number=0)]


def test_note_with_cloze_then_text(cloze_splitter):
    assert list(cloze_splitter('{c1|content} text')) == [Cloze(content='content', number=1), ' text']


def test_note_with_text_then_cloze(cloze_splitter):
    assert list(cloze_splitter('text{c1|content}')) == ['text', Cloze(content='content', number=1)]


def test_note_with_just_text(cloze_splitter):
    assert list(cloze_splitter('text')) == ['text']
