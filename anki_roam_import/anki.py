import json
import os
from dataclasses import dataclass
from typing import List

from anki.notes import Note
from anki.utils import splitFields, stripHTMLMedia
from aqt import mw
from aqt.qt import QAction
from aqt.utils import getFile, showInfo

from .roam import extract_notes_from_path
from .translate import translate_note


def plugin_main():
    action = QAction('Import Roam notes...', mw)
    action.triggered.connect(import_roam_notes_into_anki)
    mw.form.menuTools.addAction(action)


def import_roam_notes_into_anki():
    path = getFile(
        mw,
        'Open Roam export',
        cb=None,
        filter='Roam JSON export (*.zip *.json)',
        key='RoamExport',
    )

    if not path:
        return

    roam_notes = extract_notes_from_path(path)
    anki_notes = list(map(translate_note, roam_notes))
    notes_to_add = [NoteData(content, source='') for content in anki_notes]

    config = mw.addonManager.getConfig(__name__)

    added_notes = AddedNotes(added_notes_path())

    num_notes_added = 0

    note_adder = AnkiNoteAdder(mw.col, config, added_notes.read())

    for note in notes_to_add:
        card_ids = note_adder.try_add(note)
        if card_ids:
            num_notes_added += 1

    added_notes.write(list(note_adder.added_normalized_contents))

    def info():
        if not notes_to_add:
            yield 'No notes found'
            return

        if num_notes_added:
            yield f'{num_notes_added} new notes imported'

        num_duplicates = len(notes_to_add) - num_notes_added
        if num_duplicates:
            yield f'{num_duplicates} notes were imported before and were not imported again'

    showInfo(', '.join(info()) + '.')


class AddedNotes:
    def __init__(self, path):
        self.path = path

    def read(self) -> List[str]:
        if not os.path.isfile(self.path):
            return []

        with open(self.path, encoding='utf-8') as file:
            return json.load(file)

    def write(self, notes: List[str]):
        with open(self.path, encoding='utf-8', mode='w') as file:
            json.dump(notes, file)


def added_notes_path():
    module_name = __name__.split('.')[0]
    user_files_path = os.path.join(mw.addonManager.addonsFolder(module_name), 'user_files')
    os.makedirs(user_files_path, exist_ok=True)
    return os.path.join(user_files_path, 'added_notes.json')


@dataclass
class NoteData:
    content: str
    source: str


class AnkiNoteAdder:
    def __init__(self, collection, config, added_contents):
        self.collection = collection
        self.model = self.collection.models.byName(config['model_name'])
        self._find_field_indexes(config)

        self.added_normalized_contents = set(map(normalized_content, added_contents))

        note_fields = self.collection.db.list(
            'select flds from notes where mid = ?', self.model['id'])
        self.present_normalized_contents = {
            normalized_content(splitFields(fields)[self.content_field_index])
            for fields in note_fields
        }

    def _find_field_indexes(self, config):
        self.content_field_index = None
        self.source_field_index = None

        for index, field in enumerate(self.collection.models.fieldNames(self.model)):
            if field == config['content_field']:
                self.content_field_index = index
            elif field == config['source_field']:
                self.source_field_index = index

        if self.content_field_index is None or self.source_field_index is None:
            raise ValueError('Could not find content and/or source fields in model.')

    def try_add(self, note_data: NoteData) -> List:
        normalized_note_content = normalized_content(note_data.content)
        if (normalized_note_content in self.added_normalized_contents or
                normalized_note_content in self.present_normalized_contents):
            return []

        note = self._note(note_data)

        self.collection.addNote(note)

        card_ids = [card.id for card in note.cards()]

        self.added_normalized_contents.add(normalized_note_content)

        return card_ids

    def _note(self, note_data: NoteData) -> Note:
        note = Note(self.collection, self.model)
        note.fields[self.content_field_index] = note_data.content
        note.fields[self.source_field_index] = note_data.source
        return note


def normalized_content(content: str) -> str:
    return stripHTMLMedia(content).strip()
