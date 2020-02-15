import pytest

from anki_roam_import.model import JsonData, RoamNote
from anki_roam_import.roam import NoteExtractor, RoamNoteBuilder, SourceBuilder
from tests.util import mock, when


@pytest.fixture
def note_extractor(mock_roam_note_builder) -> NoteExtractor:
    return NoteExtractor(mock_roam_note_builder)


@pytest.fixture
def mock_roam_note_builder() -> RoamNoteBuilder:
    return mock(RoamNoteBuilder)


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
    roam_note = RoamNote(content, 'source')

    (when(mock_roam_note_builder)
     .called_with(block_json, [page_json])
     .then_return(roam_note))

    assert list(note_extractor([page_json])) == [roam_note]


def test_extract_from_nested_block(note_extractor, mock_roam_note_builder):
    child_block_json = block('{child}')
    parent_block_json = block('{parent}', child_block_json)
    page_json = page(parent_block_json)
    child_roam_note = RoamNote('{child}', 'child source')
    parent_roam_note = RoamNote('{parent}', 'parent source')

    (when(mock_roam_note_builder)
     .called_with(parent_block_json, [page_json])
     .then_return(parent_roam_note))

    (when(mock_roam_note_builder)
     .called_with(child_block_json, [page_json, parent_block_json])
     .then_return(child_roam_note))

    assert list(note_extractor([page_json])) == [parent_roam_note, child_roam_note]


def test_extract_without_note(note_extractor, mock_roam_note_builder):
    content = 'no note'
    block_json = block(content)
    page_json = page(block_json)

    (when(mock_roam_note_builder)
     .called_with(block_json, [page_json])
     .then_return(None))

    assert list(note_extractor([page_json])) == []


@pytest.fixture
def roam_note_builder(mock_source_builder) -> RoamNoteBuilder:
    return RoamNoteBuilder(mock_source_builder)


@pytest.fixture
def mock_source_builder() -> SourceBuilder:
    return mock(SourceBuilder)


def test_build_from_malformed_brackets(roam_note_builder):
    block_json = block('}no note{')
    page_json = page(block_json)

    assert roam_note_builder(block_json, [page_json]) is None


def test_build_from_double_brackets(roam_note_builder):
    block_json = block('{{no note}}')
    page_json = page(block_json)

    assert roam_note_builder(block_json, [page_json]) is None


def test_build_from_note(roam_note_builder, mock_source_builder):
    block_json = block('{note}')
    page_json = page(block_json)

    when(mock_source_builder).called_with(block_json, [page_json]).then_return('source')

    assert roam_note_builder(block_json, [page_json]) == RoamNote('{note}', 'source')


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


def page(*blocks: JsonData, title: str = 'title') -> JsonData:
    page_json = {'title': title}

    if blocks:
        page_json['children'] = list(blocks)

    return page_json
