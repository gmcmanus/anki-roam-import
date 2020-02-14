from dataclasses import dataclass, replace
from typing import Optional, List, Union, Iterable

from .model import RoamNote, AnkiNote
from .roam import CLOZE_PATTERN


def translate_note(
    roam_note: RoamNote,
    note_splitter: 'NoteSplitter',
    cloze_enumerator: 'ClozeEnumerator',
    note_joiner: 'NoteJoiner',
) -> AnkiNote:
    note_parts = list(note_splitter(roam_note))
    numbered_parts = cloze_enumerator(note_parts)
    return note_joiner(numbered_parts)


@dataclass
class Cloze:
    content: str
    number: Optional[int]


NotePart = Union[Cloze, str]


class NoteSplitter:
    def __call__(self, note: RoamNote) -> Iterable[NotePart]:
        index = 0

        for match in CLOZE_PATTERN.finditer(note):
            text = note[index:match.start()]
            if text:
                yield text
            index = match.end()

            match_number = match['number']
            number = int(match_number) if match_number else None

            yield Cloze(match['content'], number)

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


class NoteJoiner:
    def __call__(self, parts: Iterable[NotePart]) -> AnkiNote:
        pass
