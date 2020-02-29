import os
from dataclasses import dataclass
from typing import Any, Iterable

try:
    from anki.notes import Note
    from anki.utils import splitFields
except ModuleNotFoundError:
    # allow running tests without anki package installed
    class Note:
        def __init__(self, collection, model):
            self.fields = []

    # noinspection PyPep8Naming
    def splitFields(fields):
        return []

from .model import JsonData, AnkiNote


@dataclass
class AnkiModelNotes:
    collection: Any  # anki.collection._Collection
    model: Any  # anki.models.NoteType
    content_field_index: int
    source_field_index: int

    def add_note(self, anki_note: AnkiNote) -> None:
        note = self._note(anki_note)
        self.collection.addNote(note)

    def _note(self, anki_note: AnkiNote) -> 'Note':
        note = Note(self.collection, self.model)
        note.fields[self.content_field_index] = anki_note.anki_content
        note.fields[self.source_field_index] = anki_note.source
        return note

    def get_notes(self) -> Iterable[str]:
        note_fields = self.collection.db.list(
            'select flds from notes where mid = ?', self.model['id'])
        for fields in note_fields:
            yield splitFields(fields)[self.content_field_index]


@dataclass
class AnkiAddonData:
    anki_qt: Any  # aqt.main.AnkiQt

    def read_config(self) -> JsonData:
        return self.anki_qt.addonManager.getConfig(__name__)

    def user_files_path(self) -> str:
        module_name = __name__.split('.')[0]
        addons_directory = self.anki_qt.addonManager.addonsFolder(module_name)
        user_files_path = os.path.join(addons_directory, 'user_files')
        os.makedirs(user_files_path, exist_ok=True)
        return user_files_path


@dataclass
class AnkiCollection:
    collection: Any  # anki.collection._Collection

    def get_model_notes(
        self, model_name: str, content_field: str, source_field: str
    ) -> AnkiModelNotes:
        model = self.collection.models.byName(model_name)

        field_names = self.collection.models.fieldNames(model)
        content_field_index = field_names.index(content_field)
        source_field_index = field_names.index(source_field)

        return AnkiModelNotes(
            self.collection, model, content_field_index, source_field_index)
