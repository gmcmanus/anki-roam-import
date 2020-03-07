import pytest

from anki_roam_import.parser import (
    ParseError, ParsedValue, Parser, ParserGenerator, any_character, choose,
    exact_string, full_parser, parser_generator, zero_or_more,
)

from tests.util import mock, when


def test_parser_generator_passes_through_parsed_value():
    parsed_value = ParsedValue('value', 3)
    parser = mock(Parser)
    when(parser).called_with('string', 2).then_return(parsed_value)

    @parser_generator
    def pass_through_parser() -> ParserGenerator[str]:
        return (yield parser)

    assert pass_through_parser('string', 2) == parsed_value


def test_parser_generator_passes_through_parse_error():
    @parser_generator
    def pass_through_parser() -> ParserGenerator:
        return (yield error_parser)

    with pytest.raises(ParseError):
        pass_through_parser('string', 0)


def test_parser_generator_raises_value_error_if_start_offset_negative():
    parser = mock(Parser)

    @parser_generator
    def pass_through_parser() -> ParserGenerator[str]:
        return (yield parser)

    with pytest.raises(ValueError):
        pass_through_parser('string', -1)


def test_parser_generator_raised_value_error_if_start_offset_too_large():
    parser = mock(Parser)

    @parser_generator
    def pass_through_parser() -> ParserGenerator[str]:
        return (yield parser)

    with pytest.raises(ValueError):
        pass_through_parser('string', len('string') + 1)


def test_parser_generator_allows_start_offset_at_end_of_string():
    parsed_value = ParsedValue('value', 0)
    parser = mock(Parser)
    when(parser).called_with('string', len('string')).then_return(parsed_value)

    @parser_generator
    def pass_through_parser() -> ParserGenerator[str]:
        return (yield parser)

    assert pass_through_parser('string', len('string')) == parsed_value


def test_parser_generator_raises_value_error_if_num_characters_negative():
    parser = mock(Parser)
    parser.return_value = ParsedValue('value', -1)

    @parser_generator
    def pass_through_parser() -> ParserGenerator[str]:
        return (yield parser)

    with pytest.raises(ValueError):
        pass_through_parser('string', 0)


def test_parser_generator_raises_value_error_when_num_characters_too_large():
    parser = mock(Parser)
    parser.return_value = ParsedValue('value', len('string'))

    @parser_generator
    def pass_through_parser() -> ParserGenerator[str]:
        return (yield parser)

    with pytest.raises(ValueError):
        pass_through_parser('string', 1)


def test_parser_generator_throws_parse_error_back():
    @parser_generator
    def parser() -> ParserGenerator[str]:
        try:
            yield error_parser
        except ParseError:
            return 'value'

    assert parser('', 0) == ParsedValue('value', 0)


def test_parser_generator_send_parsed_value_back():
    parser = mock(Parser)
    parser.return_value = ParsedValue('value', 1)

    @parser_generator
    def pass_through_parser() -> ParserGenerator[str]:
        value = yield parser
        if value == 'value':
            return 'success'

    assert pass_through_parser('string', 2) == ParsedValue('success', 1)


def test_parser_generator_iterates_through_parsers():
    first_parser = mock(Parser)
    (when(first_parser)
     .called_with('string', 0)
     .then_return(ParsedValue('first value', 1)))

    second_parser = mock(Parser)
    (when(second_parser)
     .called_with('string', 1)
     .then_return(ParsedValue('second value', 2)))

    @parser_generator
    def parser() -> ParserGenerator[str]:
        first_value = yield first_parser
        second_value = yield second_parser
        return first_value, second_value

    parsed_value = parser('string', 0)
    assert parsed_value == ParsedValue(('first value', 'second value'), 3)


def test_full_parser_parses_full_string():
    @full_parser
    def parser(string: str, start_offset: int) -> ParsedValue[str]:
        return ParsedValue('value', len(string))

    assert parser('string') == 'value'


def test_full_parser_raises_parse_error_if_full_string_not_parsed():
    @full_parser
    def parser(string: str, start_offset: int) -> ParsedValue[str]:
        return ParsedValue('value', len(string) - 1)

    with pytest.raises(ParseError):
        parser('string')


def test_any_character_parses_next_character():
    assert any_character('string', 0) == ParsedValue('s', 1)
    assert any_character('string', 2) == ParsedValue('r', 1)


def test_any_character_raises_parse_error_at_end_of_string():
    with pytest.raises(ParseError):
        any_character('string', len('string'))

    with pytest.raises(ParseError):
        any_character('', 0)


def test_any_character_raises_value_error_if_start_offset_negative():
    with pytest.raises(ValueError):
        any_character('string', -1)


def test_any_character_raises_value_error_if_start_offset_too_large():
    with pytest.raises(ValueError):
        any_character('string', len('string') + 1)


def test_exact_string_parses_matching_string_from_offset():
    parser = exact_string('string')
    assert parser('astring', 1) == ParsedValue('string', len('string'))


def test_exact_string_raises_parse_error_if_string_does_not_match():
    parser = exact_string('string')
    with pytest.raises(ParseError):
        parser('string', 1)


def test_exact_string_raises_value_error_if_start_offset_negative():
    parser = exact_string('string')
    with pytest.raises(ValueError):
        parser('string', -1)


def test_exact_string_raises_value_error_if_start_offset_too_large():
    parser = exact_string('string')
    with pytest.raises(ValueError):
        parser('string', len('string') + 1)


def test_return_empty_list_when_no_match():
    parser = zero_or_more(error_parser)

    assert parser('string', 0) == ParsedValue([], 0)


def test_return_list_containing_each_match():
    sub_parser = mock(Parser)
    when(sub_parser).called_with('aab', 0).then_return(ParsedValue('A', 2))
    when(sub_parser).called_with('aab', 2).then_return(ParsedValue('B', 1))
    when(sub_parser).called_with('aab', 3).then_raise(ParseError)

    parser = zero_or_more(sub_parser)

    assert parser('aab', 0) == ParsedValue(['A', 'B'], 3)


def test_return_none_when_no_choice_matches():
    parser = choose(error_parser)

    with pytest.raises(ParseError):
        parser('string', 0)


def test_return_first_matching_choice():
    second_choice = mock(Parser)
    parser = choose(error_parser, second_choice)
    parsed_value = ParsedValue('s', 1)
    when(second_choice).called_with('string', 0).then_return(parsed_value)

    assert parser('string', 0) == parsed_value


def error_parser(string: str, index: int) -> ParsedValue[str]:
    raise ParseError
