import pytest

from anki_roam_import.translate import NoteSplitter, Cloze


@pytest.fixture
def note_splitter():
    return NoteSplitter()


def test_simple_note(note_splitter):
    assert list(note_splitter('{content}')) == [Cloze(content='content', number=None)]


def test_simple_note_with_newline(note_splitter):
    assert list(note_splitter('{con\ntent}')) == [Cloze(content='con\ntent', number=None)]


def test_note_with_cloze_number(note_splitter):
    assert list(note_splitter('{c1::content}')) == [Cloze(content='content', number=1)]


def test_note_with_cloze_then_text(note_splitter):
    assert list(note_splitter('{c1::content} text')) == [Cloze(content='content', number=1), ' text']


def test_note_with_text_then_cloze(note_splitter):
    assert list(note_splitter('text{c1::content}')) == ['text', Cloze(content='content', number=1)]


def test_note_with_just_text(note_splitter):
    assert list(note_splitter('text')) == ['text']
