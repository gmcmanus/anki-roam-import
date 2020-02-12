import re
from typing import Callable, Dict

from anki_roam_import.translate import translate_note, ClozeTranslator, NoteTranslator

from tests.util import mock, call, map_side_effect


def test_translate_simple_note():
    translation = 'anki'
    dict_cloze_translator = mock(return_value=translation)
    cloze_translator = make_cloze_translator(dict_cloze_translator)
    answer = 'roam'
    assert translate_note('{' + answer + '}', cloze_translator) == translation
    dict_cloze_translator.assert_has_calls([
        call({
            'single_bracket_answer': answer,
            'single_bracket_cloze_number': None,
            'double_bracket_answer': None,
            'double_bracket_cloze_number': None,
        }),
    ])


def make_cloze_translator(dict_cloze_translator: Callable[[Dict[str, str]], str]):
    def cloze_translator(match: re.Match):
        return dict_cloze_translator(match.groupdict())
    return cloze_translator


def test_translate_simple_note_with_newline():
    translation = 'anki'
    dict_cloze_translator = mock(return_value=translation)
    cloze_translator = make_cloze_translator(dict_cloze_translator)
    answer = 'roam\n'
    assert translate_note('{' + answer + '}', cloze_translator) == translation
    dict_cloze_translator.assert_has_calls([
        call({
            'single_bracket_answer': answer,
            'single_bracket_cloze_number': None,
            'double_bracket_answer': None,
            'double_bracket_cloze_number': None,
        }),
    ])


def test_translate_simple_note_with_two_clozes():
    first_translation = 'anki1'
    second_translation = 'anki2'
    dict_cloze_translator = mock(side_effect=[first_translation, second_translation])
    cloze_translator = make_cloze_translator(dict_cloze_translator)
    first_answer = 'roam1'
    second_answer = 'roam1'
    translation = translate_note(f'{{{first_answer}}} {{{{{second_answer}}}}}', cloze_translator)
    assert translation == f'{first_translation} {second_translation}'
    dict_cloze_translator.assert_has_calls([
        call({
            'single_bracket_answer': first_answer,
            'single_bracket_cloze_number': None,
            'double_bracket_answer': None,
            'double_bracket_cloze_number': None,
        }),
        call({
            'single_bracket_answer': None,
            'single_bracket_cloze_number': None,
            'double_bracket_answer': second_answer,
            'double_bracket_cloze_number': None,
        }),
    ])


def test_translate_note_with_double_brackets():
    translation = 'anki'
    dict_cloze_translator = mock(return_value=translation)
    cloze_translator = make_cloze_translator(dict_cloze_translator)
    answer = 'roam'
    assert translate_note('{{' + answer + '}}', cloze_translator) == translation
    dict_cloze_translator.assert_has_calls([
        call({
            'single_bracket_answer': None,
            'single_bracket_cloze_number': None,
            'double_bracket_answer': answer,
            'double_bracket_cloze_number': None,
        }),
    ])


def test_translate_cloze_with_hint():
    translation = 'anki'
    dict_cloze_translator = mock(return_value=translation)
    cloze_translator = make_cloze_translator(dict_cloze_translator)
    answer_and_hint = 'answer::hint'
    assert translate_note('{' + answer_and_hint + '}', cloze_translator) == translation
    dict_cloze_translator.assert_has_calls([
        call({
            'single_bracket_answer': answer_and_hint,
            'single_bracket_cloze_number': None,
            'double_bracket_answer': None,
            'double_bracket_cloze_number': None,
        }),
    ])


def test_translate_cloze_with_hint_and_double_brackets():
    translation = 'anki'
    dict_cloze_translator = mock(return_value=translation)
    cloze_translator = make_cloze_translator(dict_cloze_translator)
    answer_and_hint = 'answer::hint'
    assert translate_note('{{' + answer_and_hint + '}}', cloze_translator) == translation
    dict_cloze_translator.assert_has_calls([
        call({
            'single_bracket_answer': None,
            'single_bracket_cloze_number': None,
            'double_bracket_answer': answer_and_hint,
            'double_bracket_cloze_number': None,
        }),
    ])


def test_translate_note_with_custom_cloze_number():
    translation = 'anki'
    dict_cloze_translator = mock(return_value=translation)
    cloze_translator = make_cloze_translator(dict_cloze_translator)
    assert translate_note('{c2::answer}', cloze_translator) == translation
    dict_cloze_translator.assert_has_calls([
        call({
            'single_bracket_answer': 'answer',
            'single_bracket_cloze_number': '2',
            'double_bracket_answer': None,
            'double_bracket_cloze_number': None,
        }),
    ])


def test_translate_note_with_custom_cloze_number_and_hint():
    translation = 'anki'
    dict_cloze_translator = mock(return_value=translation)
    cloze_translator = make_cloze_translator(dict_cloze_translator)
    assert translate_note('{c2::answer::hint}', cloze_translator) == translation
    dict_cloze_translator.assert_has_calls([
        call({
            'single_bracket_answer': 'answer::hint',
            'single_bracket_cloze_number': '2',
            'double_bracket_answer': None,
            'double_bracket_cloze_number': None,
        }),
    ])


def test_translate_note_with_custom_cloze_number_and_double_brackets():
    translation = 'anki'
    dict_cloze_translator = mock(return_value=translation)
    cloze_translator = make_cloze_translator(dict_cloze_translator)
    assert translate_note('{{c2::answer}}', cloze_translator) == translation
    dict_cloze_translator.assert_has_calls([
        call({
            'single_bracket_answer': None,
            'single_bracket_cloze_number': None,
            'double_bracket_answer': 'answer',
            'double_bracket_cloze_number': '2',
        }),
    ])


def test_cloze_translator_simple_match():
    cloze_translator = ClozeTranslator()

    match = mock(re.Match)
    map_side_effect(match.__getitem__, {
        'single_bracket_answer': 'answer',
    })

    assert cloze_translator(match) == '{{c1::answer}}'


def test_cloze_translator_simple_match_double_brackets():
    cloze_translator = ClozeTranslator()

    match = mock(re.Match)
    map_side_effect(match.__getitem__, {
        'double_bracket_answer': 'answer',
    })

    assert cloze_translator(match) == '{{c1::answer}}'


def test_cloze_translator_preserve_cloze_numbers():
    cloze_translator = ClozeTranslator()
    match = mock(re.Match)

    map_side_effect(match.__getitem__, {
        'single_bracket_cloze_number': '2',
        'single_bracket_answer': 'answer2',
    })
    assert cloze_translator(match) == '{{c2::answer2}}'

    map_side_effect(match.__getitem__, {
        'single_bracket_answer': 'answer1',
    })
    assert cloze_translator(match) == '{{c1::answer1}}'

    map_side_effect(match.__getitem__, {
        'single_bracket_answer': 'answer3',
    })
    assert cloze_translator(match) == '{{c3::answer3}}'


def test_note_translator():
    first_cloze_translator = mock(ClozeTranslator, return_value='first translation')
    second_cloze_translator = mock(ClozeTranslator, return_value='second translation')
    cloze_translator_factory = mock(side_effect=[first_cloze_translator, second_cloze_translator])
    note_translator = NoteTranslator(cloze_translator_factory)

    assert note_translator.translate_note('{first note}') == 'first translation'
    assert note_translator.translate_note('{second note}') == 'second translation'