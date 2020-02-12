from anki_roam_import import NoteAdder, import_notes, extract_notes

from tests.util import mock, call


def test_import_two_notes():
    first_note = '{first}'
    second_note = '{second}'
    note_adder = mock(NoteAdder)

    import_notes(iter([first_note, second_note]), note_adder)

    note_adder.add_note.assert_has_calls([
        call(first_note),
        call(second_note),
    ])


def test_extract_from_empty_roam_json():
    roam_json = []

    assert list(extract_notes(roam_json)) == []


def test_extract_from_single_block():
    roam_json = [{'children': [{'string': '{note}'}]}]

    assert list(extract_notes(roam_json)) == ['{note}']
