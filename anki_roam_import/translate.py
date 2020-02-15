import re
from dataclasses import dataclass, replace
from typing import Optional, List, Union, Iterable

from .model import RoamNote, AnkiNote
from .roam import CLOZE_PATTERN


@dataclass
class NoteTranslator:
    roam_text_cleaner: 'RoamTextCleaner'
    cloze_splitter: 'ClozeSplitter'
    cloze_enumerator: 'ClozeEnumerator'
    cloze_joiner: 'ClozeJoiner'

    def __call__(self, roam_note: RoamNote) -> AnkiNote:
        clean_content = self.roam_text_cleaner(roam_note.roam_content)
        note_parts = list(self.cloze_splitter(clean_content))
        numbered_parts = self.cloze_enumerator(note_parts)
        anki_content = self.cloze_joiner(numbered_parts)

        clean_source = self.roam_text_cleaner(roam_note.source)

        return AnkiNote(anki_content=anki_content, source=clean_source)


class RoamTextCleaner:
    def __call__(self, roam_text: str) -> str:
        return ROAM_TEXT_CLEAN_PATTERN.sub('', roam_text)


ROAM_TEXT_CLEAN_PATTERN = re.compile(r'\[\[|\]\]')


@dataclass
class Cloze:
    content: str
    hint: Optional[str] = None
    number: Optional[int] = None


NotePart = Union[Cloze, str]


class ClozeSplitter:
    def __call__(self, note: str) -> Iterable[NotePart]:
        index = 0

        for match in CLOZE_PATTERN.finditer(note):
            text = note[index:match.start()]
            if text:
                yield text
            index = match.end()

            match_number = match['number']
            number = int(match_number) if match_number else None

            yield Cloze(match['content'], match['hint'], number)

        text = note[index:]
        if text:
            yield text


class ClozeEnumerator:
    def __call__(self, parts: List[NotePart]) -> Iterable[NotePart]:
        used_numbers = {
            part.number for part in parts if isinstance(part, Cloze) and has_valid_number(part)}
        next_candidate_number = 1

        for part in parts:
            if isinstance(part, Cloze) and not has_valid_number(part):
                while next_candidate_number in used_numbers:
                    next_candidate_number += 1
                part = replace(part, number=next_candidate_number)
                used_numbers.add(next_candidate_number)

            yield part


def has_valid_number(cloze: Cloze) -> bool:
    return cloze.number and cloze.number > 0


@dataclass
class ClozeJoiner:
    anki_cloze_formatter: 'AnkiClozeFormatter'

    def __call__(self, parts: Iterable[NotePart]) -> str:
        def formatted_parts():
            for part in parts:
                if isinstance(part, Cloze):
                    yield self.anki_cloze_formatter(part)
                else:
                    yield part

        return ''.join(formatted_parts())


class AnkiClozeFormatter:
    def __call__(self, numbered_cloze: Cloze) -> str:
        if not has_valid_number(numbered_cloze):
            raise ValueError

        if numbered_cloze.hint is not None:
            hint = f'::{numbered_cloze.hint}'
        else:
            hint = ''

        return '{{' + f'c{numbered_cloze.number}::{numbered_cloze.content}{hint}' + '}}'


translate_note = NoteTranslator(
    RoamTextCleaner(),
    ClozeSplitter(),
    ClozeEnumerator(),
    ClozeJoiner(AnkiClozeFormatter()),
)
