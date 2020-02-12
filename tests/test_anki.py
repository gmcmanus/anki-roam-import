from anki_roam_import.anki import NoteAdder, import_roam_notes, AnkiDeck
from anki_roam_import.translate import NoteTranslator

from tests.util import mock, call


def test_import_two_notes():
    first_note = '{first}'
    second_note = '{second}'
    note_adder = mock(NoteAdder)

    import_roam_notes(iter([first_note, second_note]), note_adder)

    note_adder.add_roam_note.assert_has_calls([
        call(first_note),
        call(second_note),
    ])


def test_add_note():
    roam_note = 'roam note'
    anki_note = 'anki note'

    note_translator = mock(NoteTranslator)
    note_translator.translate_note.return_value = anki_note
    deck = mock(AnkiDeck)
    note_adder = NoteAdder(note_translator, deck)

    note_adder.add_roam_note(roam_note)

    note_translator.translate_note.assert_has_calls([
        call(roam_note),
    ])
    deck.add_anki_note.assert_has_calls([
        call(anki_note),
    ])
