import datetime as dt

import pytest

from anki_roam_import.roam import SourceBuilder, SourceFinder, SourceFormatter, TimeFormatter

from tests.test_roam import page, block
from tests.util import when, mock


@pytest.fixture
def source_builder(mock_source_finder, mock_source_formatter) -> SourceBuilder:
    return SourceBuilder(mock_source_finder, mock_source_formatter)


@pytest.fixture
def mock_source_finder() -> SourceFinder:
    return mock(SourceFinder)


@pytest.fixture
def mock_source_formatter() -> SourceFormatter:
    return mock(SourceFormatter)


def test_source_builder(source_builder, mock_source_finder, mock_source_formatter):
    child_block_json = block('child')
    parent_block_json = block('parent', child_block_json)
    page_json = page(parent_block_json)

    (when(mock_source_finder)
     .called_with(child_block_json, [page_json, parent_block_json])
     .then_return('found source'))

    (when(mock_source_formatter)
     .called_with('found source', page_json)
     .then_return('formatted source'))

    assert source_builder(child_block_json, [page_json, parent_block_json]) == 'formatted source'


@pytest.fixture
def source_finder() -> SourceFinder:
    return SourceFinder()


@pytest.fixture
def source_formatter(mock_time_formatter) -> SourceFormatter:
    return SourceFormatter(mock_time_formatter)


@pytest.fixture
def mock_time_formatter() -> TimeFormatter:
    return mock(TimeFormatter)


def test_format_source(source_formatter, mock_time_formatter):
    create_time = 1337
    edit_time = 31337
    page_json = page(title='title', create_time=create_time, edit_time=edit_time)
    when(mock_time_formatter).called_with(create_time).then_return('[create time]')
    when(mock_time_formatter).called_with(edit_time).then_return('[edit time]')

    formatted_source = source_formatter('[source]', page_json)

    assert formatted_source == "Source: [source]\nNote from Roam page 'title', created at [create time], edited at [edit time]."


def test_time_formatter():
    time_formatter = TimeFormatter(dt.timezone.utc)
    assert time_formatter(1543212345678) == '2018-11-26T06:05:45.678+00:00'
