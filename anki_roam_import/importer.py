import json
import os.path
import re
from dataclasses import dataclass
from typing import Iterable, List

from .anki import (
    AnkiAddonData, AnkiCollection, AnkiModelNotes, is_anki_package_installed,
)
from .anki_format import make_anki_note
from .model import AnkiNote
from .roam import extract_roam_blocks, load_roam_pages

if is_anki_package_installed():
    from anki.utils import stripHTMLMedia
else:
    # allow running tests without anki package installed
    # noinspection PyPep8Naming
    def stripHTMLMedia(content): return content


@dataclass
class AnkiNoteImporter:
    addon_data: AnkiAddonData
    collection: AnkiCollection

    def import_from_path(self, path: str) -> str:
        roam_pages = load_roam_pages(path)
        roam_notes = extract_roam_blocks(roam_pages)
        notes_to_add = map(make_anki_note, roam_notes)

        num_notes_added = 0
        num_notes_ignored = 0

        added_notes_file = AddedNotesFile(added_notes_path(self.addon_data))
        added_notes = added_notes_file.read()

        normalized_notes = NormalizedNotes()
        normalized_notes.update(added_notes_file.read())

        config = self.addon_data.read_config()
        model_notes = self.collection.get_model_notes(
            config['model_name'],
            config['content_field'],
            config['source_field'],
            config['deck_name'],
        )
        note_adder = AnkiNoteAdder(model_notes, added_notes, normalized_notes)

        for note in notes_to_add:
            if note_adder.try_add(note):
                num_notes_added += 1
            else:
                num_notes_ignored += 1

        note_adder.write(added_notes_file)

        def info():
            if not num_notes_added and not num_notes_ignored:
                yield 'No notes found'
                return

            if num_notes_added:
                yield f'{num_notes_added} new notes imported'

            if num_notes_ignored:
                yield f'{num_notes_ignored} notes were imported before and were not imported again'

        return ', '.join(info()) + '.'


class NormalizedNotes:
    def __init__(self):
        self.normalized_contents = set()

    def __contains__(self, content):
        return normalized_content(content) in self.normalized_contents

    def add(self, content):
        self.normalized_contents.add(normalized_content(content))

    def update(self, contents):
        self.normalized_contents.update(map(normalized_content, contents))


def normalized_content(content: str) -> str:
    content_without_html = stripHTMLMedia(content)
    stripped_content = CHARACTERS_TO_STRIP.sub('', content_without_html)
    return ' '.join(stripped_content.split())


CHARACTERS_TO_STRIP = re.compile(r'[!"\'\(\),\-\.:;\?\[\]_`\{\}]')


class AddedNotesFile:
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


def added_notes_path(addon_data: AnkiAddonData) -> str:
    user_files_path = addon_data.user_files_path()
    return os.path.join(user_files_path, 'added_notes.json')


class AnkiNoteAdder:
    def __init__(
        self,
        model_notes: AnkiModelNotes,
        added_notes: Iterable[str],
        normalized_notes: NormalizedNotes,
    ):
        self.model_notes = model_notes
        self.added_contents = list(added_notes)
        self.normalized_notes = normalized_notes

        for note in self.model_notes.get_notes():
            self.normalized_notes.add(note)

    def try_add(self, anki_note: AnkiNote) -> bool:
        if anki_note.content in self.normalized_notes:
            return False

        self.model_notes.add_note(anki_note)
        self.normalized_notes.add(anki_note.content)
        self.added_contents.append(anki_note.content)

        return True

    def write(self, added_notes_file: AddedNotesFile):
        added_notes_file.write(self.added_contents)
