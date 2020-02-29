from aqt import mw
from aqt.qt import QAction
from aqt.utils import getFile, showInfo

from .anki import AnkiAddonData, AnkiCollection
from .importer import AnkiNoteImporter


def main():
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

    importer = AnkiNoteImporter(AnkiAddonData(mw), AnkiCollection(mw.col))
    info = importer.import_from_path(path)
    showInfo(info)
