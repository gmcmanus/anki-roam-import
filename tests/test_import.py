from anki_roam_import import NoteAdder, import_roam_notes, extract_notes, JsonData, AnkiDeck, translate_note

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


def test_extract_from_empty_roam_json():
    roam_json = []

    assert list(extract_notes(roam_json)) == []


def test_extract_from_empty_page():
    roam_json = [page()]

    assert list(extract_notes(roam_json)) == []


def test_extract_from_single_block():
    note = '{note}'
    roam_json = [page(block(note))]

    assert list(extract_notes(roam_json)) == [note]


def test_extract_from_child_blocks():
    note = '{note}'
    roam_json = [page(block('parent string', block(note)))]

    assert list(extract_notes(roam_json)) == [note]


def block(string: str, *children: JsonData) -> JsonData:
    block_json = {'string': string}
    if children:
        block_json['children'] = list(children)
    return block_json


def page(*blocks: JsonData) -> JsonData:
    if not blocks:
        return {}
    return {'children': list(blocks)}


def test_add_note():
    roam_note = 'roam note'
    anki_note = 'anki note'

    note_translator = mock(translate_note, return_value=anki_note)
    deck = mock(AnkiDeck)
    note_adder = NoteAdder(note_translator, deck)

    note_adder.add_roam_note(roam_note)

    note_translator.assert_has_calls([
        call(roam_note),
    ])
    deck.add_anki_note.assert_has_calls([
        call(anki_note),
    ])


def test_translate_simple_note():
    assert translate_note('{answer}') == '{{c1::answer}}'


def test_translate_simple_note_with_two_deletions():
    assert translate_note('{first} {second}') == '{{c1::first}} {{c2::second}}'


def test_translate_note_with_double_brackets():
    assert translate_note('{{answer}}') == '{{c1::answer}}'


def test_translate_note_with_hint():
    assert translate_note('{answer::hint}') == '{{c1::answer::hint}}'


def test_translate_note_with_custom_cloze_number():
    assert translate_note('{c2::answer}') == '{{c2::answer}}'


def test_translate_note_with_custom_cloze_number_and_double_brackets():
    assert translate_note('{{c2::answer}}') == '{{c2::answer}}'


def test_translate_note_with_custom_cloze_number_and_hint():
    assert translate_note('{c2::answer::hint}') == '{{c2::answer::hint}}'
