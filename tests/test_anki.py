from anki_roam_import.anki import make_anki_notes
from anki_roam_import.model import AnkiNote

from tests.test_roam import page, block


def test_extract_then_translate():
    source_json = block('source:: reference')
    block_json = block('{cloze} text')
    page_json = page(source_json, block_json, title='title')
    anki_notes = list(make_anki_notes([page_json]))

    assert anki_notes == [AnkiNote(
        anki_content='{{c1::cloze}} text',
        source="reference<br/>Note from Roam page 'title'.",
    )]
