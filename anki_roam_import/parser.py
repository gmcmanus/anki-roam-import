import re
from dataclasses import dataclass
from typing import (
    Any, Callable, Generator, Generic, Iterable, List, Match, Optional, TypeVar,
)

T = TypeVar('T')


@dataclass
class ParsedValue(Generic[T]):
    value: T
    num_characters: int


Parser = Callable[[str, int], ParsedValue[T]]
ParserGenerator = Generator[Parser[Any], Any, T]


class ParseError(Exception):
    pass


def parser_generator(
        generator_function: Callable[[], ParserGenerator[T]],
) -> Parser[T]:
    def parser(string: str, start_offset: int) -> ParsedValue[T]:
        check_start_offset(string, start_offset)

        generator = generator_function()
        offset = start_offset
        try:
            generated_parser = next(generator)

            while True:
                try:
                    parsed_value = generated_parser(string, offset)
                except ParseError as error:
                    generated_parser = generator.throw(type(error), error)
                else:
                    check_num_characters(parsed_value, string, offset)
                    offset += parsed_value.num_characters
                    generated_parser = generator.send(parsed_value.value)

        except StopIteration as stop:
            return ParsedValue(stop.value, num_characters=offset - start_offset)

    return parser


def check_start_offset(string: str, start_offset: int) -> None:
    if start_offset < 0 or start_offset > len(string):
        raise ValueError


def check_num_characters(
    parsed_value: ParsedValue, string: str, start_offset: int,
) -> None:
    bad_num_characters = (
        parsed_value.num_characters < 0 or
        parsed_value.num_characters > len(string) - start_offset)
    if bad_num_characters:
        raise ValueError


def full_parser(parser: Parser[T]) -> Callable[[str], T]:
    def full_parser_function(string: str) -> T:
        parsed_value = parser(string, 0)
        if parsed_value.num_characters != len(string):
            raise ParseError
        return parsed_value.value

    return full_parser_function


def any_character(string: str, start_offset: int) -> ParsedValue[str]:
    check_start_offset(string, start_offset)
    if start_offset < len(string):
        return ParsedValue(string[start_offset], 1)
    raise ParseError


def exact_string(string: str) -> Parser[str]:
    def parser(string_to_parse: str, start_offset: int) -> ParsedValue[str]:
        check_start_offset(string_to_parse, start_offset)
        if string_to_parse.startswith(string, start_offset):
            return ParsedValue(string, len(string))
        raise ParseError

    return parser


def regexp(pattern: str, flags=0) -> Parser[Match]:
    compiled_pattern = re.compile(pattern, flags)

    def parser(string: str, start_offset: int) -> ParsedValue[Match]:
        check_start_offset(string, start_offset)
        if match := compiled_pattern.match(string, start_offset):
            return ParsedValue(match, len(match.group()))
        raise ParseError

    return parser


@parser_generator
def nonnegative_integer():
    match = yield regexp('[0-9]+')
    return int(match[0])


def exact_character_once_only(character: str) -> Parser[str]:
    assert len(character) == 1

    def parser(string: str, start_offset: int) -> ParsedValue[str]:
        check_start_offset(string, start_offset)

        def matches_at(offset: int):
            return offset < len(string) and string[offset] == character

        matches = (
            matches_at(start_offset) and
            not matches_at(start_offset - 1) and
            not matches_at(start_offset + 1))

        if matches:
            return ParsedValue(character, 1)

        raise ParseError

    return parser


def start_of_string(string: str, start_offset: int) -> ParsedValue[None]:
    check_start_offset(string, start_offset)
    if start_offset == 0:
        return ParsedValue(None, 0)
    raise ParseError


def rest_of_string(string: str, start_offset: int) -> ParsedValue[str]:
    check_start_offset(string, start_offset)
    rest = string[start_offset:]
    return ParsedValue(rest, len(rest))


def choose(*parsers: Parser[T]) -> Parser[T]:
    @parser_generator
    def choose_parser() -> ParserGenerator[T]:
        for parser in parsers:
            try:
                value = yield parser
            except ParseError:
                continue
            else:
                return value

        raise ParseError

    return choose_parser


def zero_or_more(parser: Parser[T]) -> Parser[List[T]]:
    @parser_generator
    def zero_or_more_parser() -> ParserGenerator[List[T]]:
        values = []

        while True:
            try:
                value = yield parser
            except ParseError:
                return values

            values.append(value)

    return zero_or_more_parser


def optional(parser: Parser[T]) -> Parser[Optional[T]]:
    @parser_generator
    def optional_parser():
        try:
            return (yield parser)
        except ParseError:
            return None

    return optional_parser


def peek(parser: Parser[T]) -> Parser[bool]:
    def parse(string: str, start_offset: int) -> ParsedValue[bool]:
        check_start_offset(string, start_offset)

        try:
            parser(string, start_offset)
        except ParseError:
            match = False
        else:
            match = True

        return ParsedValue(match, num_characters=0)

    return parse


def delimited_text(open_delimiter: str, close_delimiter: str) -> Parser[str]:
    @parser_generator
    def parser() -> ParserGenerator[str]:
        yield exact_string(open_delimiter)

        characters = []

        while True:
            try:
                yield exact_string(close_delimiter)
            except ParseError:
                pass
            else:
                return ''.join(characters)

            character = yield any_character
            characters.append(character)

    return parser


def join_strings(value: Iterable[T]) -> List[T]:
    values = []

    for sub_value in value:
        can_join = (
            values and
            isinstance(values[-1], str) and
            isinstance(sub_value, str))

        if can_join:
            values[-1] += sub_value
        else:
            values.append(sub_value)

    return values
