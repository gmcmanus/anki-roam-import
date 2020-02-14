from dataclasses import dataclass, replace
from typing import Optional, List, Union, Iterable

from .model import RoamNote, AnkiNote
from .roam import CLOZE_PATTERN


@dataclass
class NoteTranslator:
    note_splitter: 'NoteSplitter'
    cloze_enumerator: 'ClozeEnumerator'
    note_joiner: 'NoteJoiner'

    def __call__(self, roam_note: RoamNote) -> AnkiNote:
        note_parts = list(self.note_splitter(roam_note))
        numbered_parts = self.cloze_enumerator(note_parts)
        return self.note_joiner(numbered_parts)


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


@dataclass
class NoteJoiner:
    anki_cloze_formatter: 'AnkiClozeFormatter'

    def __call__(self, parts: Iterable[NotePart]) -> AnkiNote:
        def formatted_parts():
            for part in parts:
                if isinstance(part, Cloze):
                    yield self.anki_cloze_formatter(part)
                else:
                    yield part

        return ''.join(formatted_parts())


class AnkiClozeFormatter:
    def __call__(self, numbered_cloze: Cloze) -> AnkiNote:
        if not has_valid_number(numbered_cloze):
            raise ValueError

        return '{{c' + str(numbered_cloze.number) + '::' + numbered_cloze.content + '}}'


translate_note = NoteTranslator(NoteSplitter(), ClozeEnumerator(), NoteJoiner(AnkiClozeFormatter()))
