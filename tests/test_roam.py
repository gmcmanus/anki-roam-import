from anki_roam_import.model import JsonData
from anki_roam_import.roam import extract_notes


def test_extract_from_empty_roam_json():
    roam_json = []

    assert list(extract_notes(roam_json)) == []


def test_extract_from_empty_page():
    roam_json = [page()]

    assert list(extract_notes(roam_json)) == []


def test_extract_from_single_block():
    note = '{note}'
    roam_json = [page(block(note))]

    assert list(extract_notes(roam_json)) == [note]


def test_extract_malformed_brackets():
    note = '}note{'
    roam_json = [page(block(note))]

    assert list(extract_notes(roam_json)) == []


def test_extract_from_child_blocks():
    note = '{note}'
    roam_json = [page(block('parent string', block(note)))]

    assert list(extract_notes(roam_json)) == [note]


def block(string: str, *children: JsonData) -> JsonData:
    block_json = {'string': string}
    if children:
        block_json['children'] = list(children)
    return block_json


def page(*blocks: JsonData) -> JsonData:
    if not blocks:
        return {}
    return {'children': list(blocks)}
