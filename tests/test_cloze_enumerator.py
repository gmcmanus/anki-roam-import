from dataclasses import replace

import pytest

from anki_roam_import.model import Cloze
from anki_roam_import.anki_format import ClozeEnumerator


@pytest.fixture
def cloze_enumerator():
    return ClozeEnumerator()


def test_just_text(cloze_enumerator):
    assert list(cloze_enumerator(['text'])) == ['text']


def test_just_numbered_cloze(cloze_enumerator):
    numbered_cloze = Cloze(['content'], number=2)
    assert list(cloze_enumerator([numbered_cloze])) == [numbered_cloze]


def test_just_unnumbered_cloze(cloze_enumerator):
    unnumbered_cloze = Cloze(['content'])
    assert list(cloze_enumerator([unnumbered_cloze])) == [
        replace(unnumbered_cloze, number=1)]


def test_numbered_then_unnumbered_cloze(cloze_enumerator):
    numbered_cloze = Cloze(['content2'], number=2)
    unnumbered_cloze = Cloze(['content1'])
    result = list(cloze_enumerator([numbered_cloze, unnumbered_cloze]))
    assert result == [numbered_cloze, replace(unnumbered_cloze, number=1)]


def test_unnumbered_then_numbered_cloze(cloze_enumerator):
    unnumbered_cloze = Cloze(['content2'])
    numbered_cloze = Cloze(['content1'], number=1)
    result = list(cloze_enumerator([unnumbered_cloze, numbered_cloze]))
    assert result == [replace(unnumbered_cloze, number=2), numbered_cloze]


def test_renumber_invalid_numbered_cloze(cloze_enumerator):
    cloze = Cloze(['content'], number=0)
    result = list(cloze_enumerator([cloze]))
    assert result == [replace(cloze, number=1)]
