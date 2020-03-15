import datetime as dt

import pytest

from anki_roam_import.roam import (
    SourceBuilder, SourceExtractor, SourceFinder,
    SourceFormatter, TimeFormatter,
)

from tests.test_roam import block, page
from tests.util import mock, when


@pytest.fixture
def source_builder(mock_source_finder, mock_source_formatter) -> SourceBuilder:
    return SourceBuilder(mock_source_finder, mock_source_formatter)


@pytest.fixture
def mock_source_finder() -> SourceFinder:
    return mock(SourceFinder)


@pytest.fixture
def mock_source_formatter() -> SourceFormatter:
    return mock(SourceFormatter)


def test_source_builder(
    source_builder, mock_source_finder, mock_source_formatter
):
    child_block_json = block('child')
    parent_block_json = block('parent', child_block_json)
    page_json = page(parent_block_json)

    (when(mock_source_finder)
     .called_with(child_block_json, [page_json, parent_block_json])
     .then_return('found source'))

    (when(mock_source_formatter)
     .called_with(child_block_json, 'found source', page_json)
     .then_return('formatted source'))

    formatted_source = source_builder(
        child_block_json, [page_json, parent_block_json])

    assert formatted_source == 'formatted source'


@pytest.fixture
def source_finder() -> SourceFinder:
    def source_extractor(block_json):
        if 'with source' in block_json['string']:
            return block_json['string']
        return None

    return SourceFinder(source_extractor)


def test_find_source_ignores_grandchildren(source_finder):
    grandchild = block('grandchild with source')
    child = block('child', grandchild)
    self = block('self', child)

    assert source_finder(self, []) is None


def test_find_source_prefers_first_child_with_source_to_parent(
    source_finder,
):
    self = block(
        'self',
        block('first child'),
        block('first child with source'),
        block('second child with source'),
    )
    parent = block(
        'parent with source',
        block('earlier sibling with source'),
        self,
        block('later sibling with source'),
    )

    assert source_finder(self, [parent]) == 'first child with source'


def test_find_source_ignores_siblings_with_source(source_finder):
    self = block('self')
    parent = block(
        'parent without source',
        block('earlier sibling with source'),
        self,
        block('later sibling with source'),
    )

    assert source_finder(self, [parent]) is None


def test_find_source_prefers_nearer_parent_with_source(source_finder):
    self = block('self')
    parent = block('parent', self)
    grandparent = block('grandparent with source', parent)
    great_grandparent = block('great grandparent with source', grandparent)

    source = source_finder(self, [great_grandparent, grandparent, parent])

    assert source == 'grandparent with source'


@pytest.fixture
def source_extractor() -> SourceExtractor:
    return SourceExtractor()


def test_source_extractor_without_string(source_extractor):
    assert source_extractor({}) is None


def test_source_extractor_with_upper_case_source(source_extractor):
    block_json = block('Source:: reference')
    assert source_extractor(block_json) == 'reference'


def test_source_extractor_with_lower_case_source(source_extractor):
    block_json = block('source:: reference')
    assert source_extractor(block_json) == 'reference'


def test_source_extractor_with_one_colon(source_extractor):
    block_json = block('Source: reference')
    assert source_extractor(block_json) == 'reference'


def test_source_extractor_with_extra_whitespace(source_extractor):
    block_json = block('  Source  :  :  reference  ')
    assert source_extractor(block_json) == 'reference'


def test_source_extractor_with_extra_text(source_extractor):
    block_json = block('text source: reference ')
    assert source_extractor(block_json) is None


@pytest.fixture
def source_formatter(mock_time_formatter) -> SourceFormatter:
    return SourceFormatter(mock_time_formatter)


@pytest.fixture
def mock_time_formatter() -> TimeFormatter:
    return mock(TimeFormatter)


def test_format_source(source_formatter, mock_time_formatter):
    create_time = 1337
    edit_time = 31337
    page_json = page(title='title')
    block_json = block('note', create_time=create_time, edit_time=edit_time)
    (when(mock_time_formatter)
     .called_with(create_time)
     .then_return('[create time]'))
    (when(mock_time_formatter)
     .called_with(edit_time)
     .then_return('[edit time]'))

    formatted_source = source_formatter(block_json, '[source]', page_json)

    assert formatted_source == "[source]\nNote from Roam page 'title', created at [create time], edited at [edit time]."


def test_time_formatter():
    time_formatter = TimeFormatter(dt.timezone.utc)
    assert time_formatter(1543212345678) == '2018-11-26T06:05:45.678+00:00'
