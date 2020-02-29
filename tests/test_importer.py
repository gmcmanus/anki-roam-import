import json
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import call

import pytest

from anki_roam_import.anki import AnkiAddonData, AnkiModelNotes, AnkiCollection
from anki_roam_import.importer import AnkiNoteImporter
from anki_roam_import.model import JsonData, AnkiNote

from tests.test_roam import page, block
from tests.util import when, mock


@dataclass
class JsonFile:
    path: Path

    def write_json(self, json_data: JsonData) -> None:
        json.dump(json_data, self.path.open('w', encoding='utf-8'))


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


def test_import_cloze_note_with_source(
        roam_json_file, addon_data, anki_collection, anki_model_notes):
    roam_json_file.write_json([page(
        block('source:: reference'),
        block('{cloze} text'),
        title='title',
    )])

    importer = AnkiNoteImporter(addon_data, anki_collection)
    info = importer.import_from_path(str(roam_json_file.path))

    anki_model_notes.add_note.assert_has_calls([
        call(AnkiNote(
            anki_content='{{c1::cloze}} text',
            source="reference<br/>Note from Roam page 'title'.",
        )),
    ])

    assert info == '1 new notes imported.'
