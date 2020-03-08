import json
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import call

import pytest

from anki_roam_import.anki import AnkiAddonData, AnkiCollection, AnkiModelNotes
from anki_roam_import.importer import AnkiNoteImporter
from anki_roam_import.model import AnkiNote, JsonData

from tests.test_roam import block, page
from tests.util import mock, when


@dataclass
class JsonFile:
    path: Path

    def write_json(self, json_data: JsonData) -> None:
        json.dump(json_data, self.path.open('w', encoding='utf-8'))

    def write_blocks(self, *contents: str, title: str = None) -> None:
        blocks = map(block, contents)
        self.write_json([page(*blocks, title=title)])


@pytest.fixture
def roam_json_file(tmp_path_factory) -> JsonFile:
    return JsonFile(tmp_path_factory.mktemp('roam') / 'roam.json')


MODEL_NAME = 'model name'
CONTENT_FIELD = 'content field name'
SOURCE_FIELD = 'source field name'


@pytest.fixture
def addon_data(tmp_path_factory) -> AnkiAddonData:
    anki_addon_data = mock(AnkiAddonData)

    anki_addon_data.read_config.return_value = {
        'model_name': MODEL_NAME,
        'content_field': CONTENT_FIELD,
        'source_field': SOURCE_FIELD,
    }

    user_files_path = tmp_path_factory.mktemp('user_files')
    anki_addon_data.user_files_path.return_value = str(user_files_path)

    return anki_addon_data


@pytest.fixture
def anki_collection(anki_model_notes) -> AnkiCollection:
    collection = mock(AnkiCollection)
    (when(collection.get_model_notes)
     .called_with(MODEL_NAME, CONTENT_FIELD, SOURCE_FIELD)
     .then_return(anki_model_notes))
    return collection


@pytest.fixture
def anki_model_notes() -> AnkiModelNotes:
    return mock(AnkiModelNotes)


@pytest.fixture
def anki_note_importer(addon_data, anki_collection):
    return AnkiNoteImporter(addon_data, anki_collection)


def test_import_cloze_note_with_source(
    roam_json_file, addon_data, anki_collection, anki_model_notes,
):
    roam_json_file.write_blocks(
        'source:: reference',
        '{cloze} text',
        title='title',
    )

    importer = AnkiNoteImporter(addon_data, anki_collection)
    info = importer.import_from_path(str(roam_json_file.path))

    anki_model_notes.add_note.assert_has_calls([
        call(AnkiNote(
            content='{{c1::cloze}} text',
            source="reference<br/>Note from Roam page &#x27;title&#x27;.",
        )),
    ])
    assert info == '1 new notes imported.'


def test_translate_latex_math(
    roam_json_file, anki_note_importer, anki_model_notes,
):
    roam_json_file.write_blocks(
        r'$$\textrm{outside cloze}$$ and {inside $$\textrm{cloze}$$}',
    )

    info = anki_note_importer.import_from_path(str(roam_json_file.path))

    anki_model_notes.add_note.assert_has_calls([
        call(AnkiNote(
            content=r'\(\textrm{outside cloze}\) and {{c1::inside \(\textrm{cloze}\)}}',
            source="Note from Roam page &#x27;title&#x27;.",
        )),
    ])
    assert info == '1 new notes imported.'


def test_translate_code(
    roam_json_file, anki_note_importer, anki_model_notes,
):
    roam_json_file.write_blocks('`code` and {`code` in cloze}')

    info = anki_note_importer.import_from_path(str(roam_json_file.path))

    anki_model_notes.add_note.assert_has_calls([
        call(AnkiNote(
            content='<code>code</code> and {{c1::<code>code</code> in cloze}}',
            source="Note from Roam page &#x27;title&#x27;.",
        )),
    ])
    assert info == '1 new notes imported.'


def test_do_not_add_note_with_brackets_inside_code(
    roam_json_file, anki_note_importer, anki_model_notes,
):
    roam_json_file.write_blocks('```{not cloze}```')

    info = anki_note_importer.import_from_path(str(roam_json_file.path))

    anki_model_notes.add_note.assert_not_called()
    assert info == 'No notes found.'


def test_format_as_html(
        roam_json_file, anki_note_importer, anki_model_notes,
):
    roam_json_file.write_blocks(
        'source:: source  & ',
        '{<cloze> } &  text ',
        title=' &  title ',
    )

    info = anki_note_importer.import_from_path(str(roam_json_file.path))

    anki_model_notes.add_note.assert_has_calls([
        call(AnkiNote(
            content='{{c1::&lt;cloze&gt; }} &amp;&nbsp;&nbsp;text ',
            source="source&nbsp;&nbsp;&amp;<br/>Note from Roam page &#x27; &amp;&nbsp;&nbsp;title &#x27;.",
        )),
    ])
    assert info == '1 new notes imported.'
