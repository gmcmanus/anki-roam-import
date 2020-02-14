from dataclasses import replace

from anki_roam_import.translate import (
    NoteTranslator,
    Cloze,
    NoteSplitter,
    ClozeEnumerator,
    NoteJoiner,
    translate_note,
    RoamNoteCleaner,
)

from tests.util import mock, when


def test_translate_simple_note():
    roam_note = '{[[content]]}'

    note_cleaner = mock(RoamNoteCleaner)
    clean_note = '{content}'
    when(note_cleaner).called_with(roam_note).then_return(clean_note)

    note_splitter = mock(NoteSplitter)
    cloze = Cloze('content')
    when(note_splitter).called_with(clean_note).then_return([cloze])

    cloze_enumerator = mock(ClozeEnumerator)
    numbered_cloze = replace(cloze, number=1)
    when(cloze_enumerator).called_with([cloze]).then_return([numbered_cloze])

    note_joiner = mock(NoteJoiner)
    joined_note = '{{c1::content}}'
    when(note_joiner).called_with([numbered_cloze]).then_return(joined_note)

    note_translator = NoteTranslator(note_cleaner, note_splitter, cloze_enumerator, note_joiner)

    assert note_translator(roam_note) == joined_note


def test_roam_note_cleaner():
    cleaner = RoamNoteCleaner()
    assert cleaner('[[content]]') == 'content'
    assert cleaner('[content]') == '[content]'


def test_translate_note_wiring():
    assert translate_note('{content} text') == '{{c1::content}} text'
