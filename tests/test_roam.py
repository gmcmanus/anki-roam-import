from typing import Callable, List

import pytest

from anki_roam_import.model import Cloze, JsonData, RoamBlock, RoamPart
from anki_roam_import.roam import (
    BlockExtractor, RoamBlockBuilder, SourceBuilder,
)
from tests.util import mock, when


@pytest.fixture
def note_extractor(mock_roam_note_builder) -> BlockExtractor:
    return BlockExtractor(mock_roam_note_builder)


@pytest.fixture
def mock_roam_note_builder() -> RoamBlockBuilder:
    return mock(RoamBlockBuilder)


def test_extract_from_empty_roam_json(note_extractor):
    roam_json = []

    assert list(note_extractor(roam_json)) == []


def test_extract_from_empty_page(note_extractor):
    roam_json = [page()]

    assert list(note_extractor(roam_json)) == []


def test_extract_from_single_block(note_extractor, mock_roam_note_builder):
    content = '{note}'
    block_json = block(content)
    page_json = page(block_json)
    roam_note = RoamBlock([Cloze(['cloze content'])], 'source')

    (when(mock_roam_note_builder)
     .called_with(block_json, [page_json])
     .then_return(roam_note))

    assert list(note_extractor([page_json])) == [roam_note]


def test_extract_from_nested_block(note_extractor, mock_roam_note_builder):
    child_block_json = block('{child}')
    parent_block_json = block('{parent}', child_block_json)
    page_json = page(parent_block_json)
    child_roam_note = RoamBlock(
        [Cloze(['child cloze content'])], 'child source')
    parent_roam_note = RoamBlock(
        [Cloze(['parent cloze content'])], 'parent source')

    (when(mock_roam_note_builder)
     .called_with(parent_block_json, [page_json])
     .then_return(parent_roam_note))

    (when(mock_roam_note_builder)
     .called_with(child_block_json, [page_json, parent_block_json])
     .then_return(child_roam_note))

    assert list(note_extractor([page_json])) == [
        parent_roam_note, child_roam_note]


def test_extract_without_note(note_extractor, mock_roam_note_builder):
    content = 'no note'
    block_json = block(content)
    page_json = page(block_json)

    (when(mock_roam_note_builder)
     .called_with(block_json, [page_json])
     .then_return(None))

    assert list(note_extractor([page_json])) == []


@pytest.fixture
def roam_note_builder(
    mock_roam_parser, mock_source_builder,
) -> RoamBlockBuilder:
    return RoamBlockBuilder(mock_roam_parser, mock_source_builder)


@pytest.fixture
def mock_roam_parser() -> Callable[[str], List[RoamPart]]:
    return mock(Callable[[str], List[RoamPart]])


@pytest.fixture
def mock_source_builder() -> SourceBuilder:
    return mock(SourceBuilder)


def test_return_none_when_no_cloze_part(roam_note_builder, mock_roam_parser):
    block_json = block('no note')
    parent_json = page(block_json)
    when(mock_roam_parser).called_with('no note').then_return(['no note'])

    assert roam_note_builder(block_json, [parent_json]) is None


def test_return_note_when_cloze_part(
    roam_note_builder, mock_roam_parser, mock_source_builder,
):
    block_json = block('{block text}')
    parent_json = page(block_json)
    note_parts = [Cloze(['cloze content'])]
    when(mock_roam_parser).called_with('{block text}').then_return(note_parts)
    (when(mock_source_builder)
     .called_with(block_json, [parent_json])
     .then_return('source'))

    roam_note = roam_note_builder(block_json, [parent_json])

    assert roam_note == RoamBlock(note_parts, 'source')


def block(
    string: str,
    *children: JsonData,
    create_time: int = None,
    edit_time: int = None,
) -> JsonData:
    block_json = {'string': string}

    if children:
        block_json['children'] = list(children)

    if create_time is not None:
        block_json['create-time'] = create_time

    if edit_time is not None:
        block_json['edit-time'] = edit_time

    return block_json


def page(*blocks: JsonData, title: str = None) -> JsonData:
    if title is None:
        title = 'title'

    page_json = {'title': title}

    if blocks:
        page_json['children'] = list(blocks)

    return page_json
