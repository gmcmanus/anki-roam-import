import pytest

from anki_roam_import.translate import NoteJoiner, Cloze, AnkiClozeFormatter

from tests.util import mock, when


@pytest.fixture
def note_joiner(mock_anki_cloze_formatter) -> NoteJoiner:
    return NoteJoiner(mock_anki_cloze_formatter)


@pytest.fixture
def mock_anki_cloze_formatter():
    return mock(AnkiClozeFormatter)


def test_join_single_cloze(note_joiner, mock_anki_cloze_formatter):
    cloze = Cloze('content', number=1)
    formatted_cloze = '{{c1::content}}'
    when(mock_anki_cloze_formatter).called_with(cloze).then_return(formatted_cloze)
    assert note_joiner([cloze]) == formatted_cloze


def test_join_single_text(note_joiner):
    assert note_joiner(['text']) == 'text'


def test_join_cloze_and_text(note_joiner, mock_anki_cloze_formatter):
    cloze = Cloze('content', number=1)
    formatted_cloze = '{{c1::content}}'
    when(mock_anki_cloze_formatter).called_with(cloze).then_return(formatted_cloze)
    assert note_joiner([cloze, 'text']) == formatted_cloze + 'text'


@pytest.fixture
def anki_cloze_formatter() -> AnkiClozeFormatter:
    return AnkiClozeFormatter()


def test_format_numbered_cloze(anki_cloze_formatter):
    assert anki_cloze_formatter(Cloze('content', number=1)) == '{{c1::content}}'


def test_format_unnumbered_cloze(anki_cloze_formatter):
    with pytest.raises(ValueError):
        anki_cloze_formatter(Cloze('content', number=None))


def test_format_zero_numbered_cloze(anki_cloze_formatter):
    with pytest.raises(ValueError):
        anki_cloze_formatter(Cloze('content', number=0))


