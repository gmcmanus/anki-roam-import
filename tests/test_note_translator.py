from dataclasses import replace

from anki_roam_import.translate import (
    NoteTranslator,
    Cloze,
    NoteSplitter,
    ClozeEnumerator,
    NoteJoiner,
)

from tests.util import mock, when


def test_translate_simple_note():
    content = 'content'
    note = '{' + content + '}'

    note_splitter = mock(NoteSplitter)
    cloze = Cloze(content, number=None)
    when(note_splitter).called_with(note).then_return([cloze])

    cloze_enumerator = mock(ClozeEnumerator)
    numbered_cloze = replace(cloze, number=1)
    when(cloze_enumerator).called_with([cloze]).then_return([numbered_cloze])

    note_joiner = mock(NoteJoiner)
    joined_note = '{{c1::content}}'
    when(note_joiner).called_with([numbered_cloze]).then_return(joined_note)

    note_translator = NoteTranslator(note_splitter, cloze_enumerator, note_joiner)

    assert note_translator(note) == joined_note
