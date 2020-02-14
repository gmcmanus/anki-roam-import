from dataclasses import dataclass
from typing import Any


# PyCharm doesn't infer well with:
# JsonData = Union[None, bool, str, float, int, List['JsonData'], Dict[str, 'JsonData']]
JsonData = Any


@dataclass
class RoamNote:
    content: str
    source: str


AnkiNote = str
