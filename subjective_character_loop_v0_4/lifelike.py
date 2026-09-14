from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Optional


_WORD = re.compile(r"[A-Za-z0-9]+(?:['’][A-Za-z0-9]+)?")
_UNFINISHED_MARKERS = (
    "?",
    "still ",
    "still don't",
    "still do not",
    "don't know",
    "do not know",
    "not sure",
    "need to",
    "have to",
    "should ",
    "want to",
    "can't ",
    "cannot ",
    "bothers me",
    "keeps bothering me",
    "keep coming back",
    "not ready",
    "figure out",
    "work out",
    "wonder ",
    "whether ",
    "why ",
    "how ",
    "maybe ",
    "perhaps ",
    "later",
)
_CLOSURE_MARKERS = (
    "that settles it",
    "i have decided",
    "i've decided",
    "i understand now",
    "i know what to do now",
    "i can let this go",
    "i can leave this behind",
    "it doesn't matter anymore",
    "it does not matter anymore",
    "i was wrong about that",
    "i was mistaken about that",
)
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "because", "been", "but", "by",
    "do", "for", "from", "had", "has", "have", "i", "if", "in", "is", "it", "me",
    "my", "of", "on", "or", "so", "that", "the", "this", "to", "was", "were", "what",
    "when", "where", "which", "who", "with", "would", "yet",
}


def _tokens(text: str) -> set[str]:
    return {
        token.lower().replace("’", "'")
        for token in _WORD.findall(text)
        if token.lower() not in _STOPWORDS and len(token) > 2
    }


def _similarity(a: str, b: str) -> float:
    aa, bb = _tokens(a), _tokens(b)
    if not aa or not bb:
        return 0.0
    return len(aa & bb) / len(aa | bb)


@dataclass
class LingeringConcern:
    text: str
    alive: bool = True

    def to_json(self) -> dict[str, object]:
        return {"text": self.text, "alive": self.alive}

    @classmethod
    def from_json(cls, data: object) -> Optional["LingeringConcern"]:
        if not isinstance(data, dict):
            return None
        text = str(data.get("text", "")).strip()
        if not text:
            return None
        return cls(text=text, alive=bool(data.get("alive", True)))


class FirstPersonLife:
    """Persistent first-person carryover expressed as language, not telemetry.

    The substrate keeps only character-readable natural-language material. Python data
    structures exist for persistence and deduplication, but the character-facing state
    is always rendered as ordinary first-person language. It is deliberately small: the
    first responsibility is to let unfinished life remain unfinished across quiet turns
    and restarts instead of making each cognitive cycle feel freshly instantiated.
    """

    def __init__(self, concerns: Optional[Iterable[LingeringConcern]] = None) -> None:
        self.concerns = list(concerns or [])

    @classmethod
    def from_json(cls, data: object) -> "FirstPersonLife":
        if not isinstance(data, dict):
            return cls()
        concerns = []
        for raw in data.get("concerns", []):
            concern = LingeringConcern.from_json(raw)
            if concern is not None:
                concerns.append(concern)
        return cls(concerns)

    def to_json(self) -> dict[str, object]:
        return {"concerns": [concern.to_json() for concern in self.concerns]}

    @staticmethod
    def _looks_unfinished(text: str) -> bool:
        low = f" {text.lower().strip()} "
        return any(marker in low for marker in _UNFINISHED_MARKERS)

    @staticmethod
    def _looks_closed(text: str) -> bool:
        low = text.lower().strip()
        return any(marker in low for marker in _CLOSURE_MARKERS)

    def _nearest_alive(self, text: str, minimum: float = 0.28) -> Optional[LingeringConcern]:
        best: Optional[LingeringConcern] = None
        best_score = minimum
        for concern in self.concerns:
            if not concern.alive:
                continue
            score = _similarity(text, concern.text)
            if score >= best_score:
                best, best_score = concern, score
        return best

    def observe_thought(self, text: str) -> None:
        value = " ".join(text.split()).strip()
        if not value:
            return

        if self._looks_closed(value):
            nearest = self._nearest_alive(value, minimum=0.18)
            if nearest is not None:
                nearest.alive = False
            return

        if not self._looks_unfinished(value):
            return

        nearest = self._nearest_alive(value, minimum=0.45)
        if nearest is not None:
            # Preserve the newest natural formulation without multiplying the concern.
            nearest.text = value
            return
        self.concerns.append(LingeringConcern(value))

    def process_experience(self, text: str, provenance: str) -> list[str]:
        # Cycle 5 does not reshape perception yet. Later cycles can add habituation,
        # cue-triggered prospective memory, and spontaneous recurrence behind this API.
        value = text.strip()
        return [value] if value else []

    def observe_memory(self, text: str) -> None:
        return None

    def advance(self, seconds: float, rng: object = None) -> list[str]:
        return []

    def alive_concerns(self) -> list[str]:
        return [concern.text for concern in self.concerns if concern.alive]

    def render_private_context(self, limit: int = 3) -> str:
        alive = self.alive_concerns()[-max(0, int(limit)) :]
        if not alive:
            return ""
        if len(alive) == 1:
            return (
                "Something is still quietly unresolved for me. I do not have to think "
                f"about it right now, but I am still carrying this: {alive[0]}"
            )
        joined = "\n".join(f"I am still carrying this: {text}" for text in alive)
        return (
            "A few things remain unresolved in the background of my life. They do not "
            "all require attention now, and I do not have to resolve them merely because "
            "they are present.\n" + joined
        )
