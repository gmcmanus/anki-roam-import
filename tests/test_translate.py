import re
from dataclasses import replace

from anki_roam_import.translate import (
    translate_note,
    Cloze,
    NoteSplitter,
    ClozeEnumerator,
    NoteJoiner,
)

from tests.util import mock, call, when


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

    assert translate_note(note, note_splitter, cloze_enumerator, note_joiner) == joined_note


def test_translate_simple_note_with_two_clozes():
    first_translation = 'anki1'
    second_translation = 'anki2'
    dict_cloze_translator = mock(side_effect=[first_translation, second_translation])
    cloze_translator = make_cloze_translator(dict_cloze_translator)
    first_answer = 'roam1'
    second_answer = 'roam1'
    translation = translate_note(f'{{{first_answer}}} {{{second_answer}}}', cloze_translator)
    assert translation == f'{first_translation} {second_translation}'
    dict_cloze_translator.assert_has_calls([
        call({
            'answer': first_answer,
            'cloze_number': None,
        }),
        call({
            'answer': second_answer,
            'cloze_number': None,
        }),
    ])


def test_translate_note_with_double_brackets():
    note = '{{roam}}'
    assert translate_note(note, mock(ClozeTranslator, return_value='')) == note


def test_translate_note_with_custom_cloze_number():
    translation = 'anki'
    dict_cloze_translator = mock(return_value=translation)
    cloze_translator = make_cloze_translator(dict_cloze_translator)
    assert translate_note('{c2::answer}', cloze_translator) == translation
    dict_cloze_translator.assert_has_calls([
        call({
            'answer': 'answer',
            'cloze_number': '2',
        }),
    ])


def test_translate_note_with_custom_cloze_number_and_hint():
    translation = 'anki'
    dict_cloze_translator = mock(return_value=translation)
    cloze_translator = make_cloze_translator(dict_cloze_translator)
    assert translate_note('{c2::answer::hint}', cloze_translator) == translation
    dict_cloze_translator.assert_has_calls([
        call({
            'answer': 'answer::hint',
            'cloze_number': '2',
        }),
    ])


def test_cloze_translator_simple_match():
    cloze_translator = ClozeTranslator()

    match = mock(re.Match)
    map_side_effect(match.__getitem__, {
        'answer': 'answer',
    })

    assert cloze_translator(match) == '{{c1::answer}}'


def test_cloze_translator_preserve_cloze_numbers():
    cloze_translator = ClozeTranslator()
    match = mock(re.Match)

    map_side_effect(match.__getitem__, {
        'cloze_number': '2',
        'answer': 'answer2',
    })
    assert cloze_translator(match) == '{{c2::answer2}}'

    map_side_effect(match.__getitem__, {
        'answer': 'answer1',
    })
    assert cloze_translator(match) == '{{c1::answer1}}'

    map_side_effect(match.__getitem__, {
        'answer': 'answer3',
    })
    assert cloze_translator(match) == '{{c3::answer3}}'


def test_note_translator():
    first_cloze_translator = mock(ClozeTranslator, return_value='first translation')
    second_cloze_translator = mock(ClozeTranslator, return_value='second translation')
    cloze_translator_factory = mock(side_effect=[first_cloze_translator, second_cloze_translator])
    note_translator = NoteTranslator(cloze_translator_factory)

    assert note_translator.translate_note('{first note}') == 'first translation'
    assert note_translator.translate_note('{second note}') == 'second translation'
