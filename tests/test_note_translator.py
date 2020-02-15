from dataclasses import replace

from anki_roam_import.model import RoamNote, AnkiNote
from anki_roam_import.translate import (
    NoteTranslator,
    Cloze,
    ClozeSplitter,
    ClozeEnumerator,
    ClozeJoiner,
    RoamTextCleaner,
)

from tests.util import mock, when


def test_translate_simple_note():
    roam_note = RoamNote('{[[content]]}', '[[source]]')

    text_cleaner = mock(RoamTextCleaner)
    when(text_cleaner).called_with(roam_note.roam_content).then_return('{content}')
    when(text_cleaner).called_with(roam_note.source).then_return('source')

    cloze_splitter = mock(ClozeSplitter)
    cloze = Cloze('content')
    when(cloze_splitter).called_with('{content}').then_return([cloze])

    cloze_enumerator = mock(ClozeEnumerator)
    numbered_cloze = replace(cloze, number=1)
    when(cloze_enumerator).called_with([cloze]).then_return([numbered_cloze])

    cloze_joiner = mock(ClozeJoiner)
    joined_note = '{{c1::content}}'
    when(cloze_joiner).called_with([numbered_cloze]).then_return(joined_note)

    note_translator = NoteTranslator(text_cleaner, cloze_splitter, cloze_enumerator, cloze_joiner)

    assert note_translator(roam_note) == AnkiNote(joined_note, 'source')


def test_roam_text_cleaner():
    cleaner = RoamTextCleaner()
    assert cleaner('[[content]]') == 'content'
    assert cleaner('[content]') == '[content]'
