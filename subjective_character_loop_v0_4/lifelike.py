from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Optional


_WORD = re.compile(r"[A-Za-z0-9]+(?:['’][A-Za-z0-9]+)?")
_UNFINISHED_MARKERS = (
    "?", "still ", "still don't", "still do not", "don't know", "do not know",
    "not sure", "need to", "have to", "should ", "want to", "can't ", "cannot ",
    "bothers me", "keeps bothering me", "keep coming back", "not ready", "figure out",
    "work out", "wonder ", "whether ", "why ", "how ", "maybe ", "perhaps ", "later",
)
_CLOSURE_MARKERS = (
    "that settles it", "i have decided", "i've decided", "i understand now",
    "i know what to do now", "i can let this go", "i can leave this behind",
    "it doesn't matter anymore", "it does not matter anymore", "i was wrong about that",
    "i was mistaken about that",
)
_TENSION_MARKERS = (
    " but ", "although ", "even though ", "part of me", "at the same time",
    "on the other hand", "and yet ", "still, part of me", "i also want",
)
_TENSION_RESOLUTION_MARKERS = (
    "i have decided", "i've decided", "i am choosing", "i'm choosing",
    "i no longer feel torn", "i know which matters more", "i know which one matters more",
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
    intersection = len(aa & bb)
    jaccard = intersection / len(aa | bb)
    overlap = intersection / min(len(aa), len(bb))
    return max(jaccard, overlap * 0.72)


def _normalized(text: str) -> str:
    return " ".join(text.lower().split())


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


@dataclass
class InnerTension:
    text: str
    alive: bool = True

    def to_json(self) -> dict[str, object]:
        return {"text": self.text, "alive": self.alive}

    @classmethod
    def from_json(cls, data: object) -> Optional["InnerTension"]:
        if not isinstance(data, dict):
            return None
        text = str(data.get("text", "")).strip()
        if not text:
            return None
        return cls(text=text, alive=bool(data.get("alive", True)))


@dataclass
class FamiliarExperience:
    text: str
    repetitions: int = 1

    def to_json(self) -> dict[str, object]:
        return {"text": self.text, "repetitions": max(1, int(self.repetitions))}

    @classmethod
    def from_json(cls, data: object) -> Optional["FamiliarExperience"]:
        if not isinstance(data, dict):
            return None
        text = str(data.get("text", "")).strip()
        if not text:
            return None
        return cls(text=text, repetitions=max(1, int(data.get("repetitions", 1))))


@dataclass
class ProspectiveIntention:
    text: str
    cue: str
    active: bool = False

    def to_json(self) -> dict[str, object]:
        return {"text": self.text, "cue": self.cue, "active": self.active}

    @classmethod
    def from_json(cls, data: object) -> Optional["ProspectiveIntention"]:
        if not isinstance(data, dict):
            return None
        text = str(data.get("text", "")).strip()
        cue = str(data.get("cue", "")).strip()
        if not text or not cue:
            return None
        return cls(text=text, cue=cue, active=bool(data.get("active", False)))


class FirstPersonLife:
    """Persistent first-person carryover expressed as language, not telemetry."""

    def __init__(
        self,
        concerns: Optional[Iterable[LingeringConcern]] = None,
        familiar: Optional[Iterable[FamiliarExperience]] = None,
        tensions: Optional[Iterable[InnerTension]] = None,
        intentions: Optional[Iterable[ProspectiveIntention]] = None,
        returning_text: str = "",
        recurrence_refractory: bool = False,
    ) -> None:
        self.concerns = list(concerns or [])
        self.familiar = list(familiar or [])
        self.tensions = list(tensions or [])
        self.intentions = list(intentions or [])
        self.returning_text = returning_text.strip()
        self.recurrence_refractory = bool(recurrence_refractory)

    @classmethod
    def from_json(cls, data: object) -> "FirstPersonLife":
        if not isinstance(data, dict):
            return cls()
        concerns = [item for raw in data.get("concerns", []) if (item := LingeringConcern.from_json(raw))]
        familiar = [item for raw in data.get("familiar", []) if (item := FamiliarExperience.from_json(raw))]
        tensions = [item for raw in data.get("tensions", []) if (item := InnerTension.from_json(raw))]
        intentions = [item for raw in data.get("intentions", []) if (item := ProspectiveIntention.from_json(raw))]
        return cls(
            concerns,
            familiar,
            tensions,
            intentions,
            returning_text=str(data.get("returning_text", "")),
            recurrence_refractory=bool(data.get("recurrence_refractory", False)),
        )

    def to_json(self) -> dict[str, object]:
        return {
            "concerns": [concern.to_json() for concern in self.concerns],
            "familiar": [item.to_json() for item in self.familiar],
            "tensions": [tension.to_json() for tension in self.tensions],
            "intentions": [intention.to_json() for intention in self.intentions],
            "returning_text": self.returning_text,
            "recurrence_refractory": self.recurrence_refractory,
        }

    @staticmethod
    def _looks_unfinished(text: str) -> bool:
        low = f" {text.lower().strip()} "
        return any(marker in low for marker in _UNFINISHED_MARKERS)

    @staticmethod
    def _looks_closed(text: str) -> bool:
        low = text.lower().strip()
        return any(marker in low for marker in _CLOSURE_MARKERS)

    @staticmethod
    def _looks_tense(text: str) -> bool:
        low = f" {text.lower().strip()} "
        return any(marker in low for marker in _TENSION_MARKERS)

    @staticmethod
    def _looks_tension_resolution(text: str) -> bool:
        low = text.lower().strip()
        return any(marker in low for marker in _TENSION_RESOLUTION_MARKERS)

    @staticmethod
    def _prospective_cue(text: str) -> str:
        value = " ".join(text.split()).strip()
        for pattern in (
            r"(?i)^when\s+(.+?),\s*",
            r"(?i)^if\s+(.+?),\s*",
            r"(?i)^next\s+time\s+(.+?),\s*",
        ):
            match = re.match(pattern, value)
            if match:
                return match.group(1).strip()
        return ""

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

    def _nearest_tension(self, text: str, minimum: float = 0.34) -> Optional[InnerTension]:
        best: Optional[InnerTension] = None
        best_score = minimum
        for tension in self.tensions:
            if not tension.alive:
                continue
            score = _similarity(text, tension.text)
            if score >= best_score:
                best, best_score = tension, score
        return best

    def _remember_intention(self, text: str, cue: str) -> None:
        value = _normalized(text)
        for intention in self.intentions:
            if _normalized(intention.text) == value:
                return
            if _similarity(intention.text, text) >= 0.62 and _similarity(intention.cue, cue) >= 0.55:
                intention.text = text
                intention.cue = cue
                return
        self.intentions.append(ProspectiveIntention(text=text, cue=cue))

    def observe_thought(self, text: str) -> None:
        value = " ".join(text.split()).strip()
        if not value:
            return

        cue = self._prospective_cue(value)
        if cue:
            self._remember_intention(value, cue)
            return

        if self._looks_tension_resolution(value):
            nearest_tension = self._nearest_tension(value, minimum=0.20)
            if nearest_tension is not None:
                nearest_tension.alive = False
        elif self._looks_tense(value):
            nearest_tension = self._nearest_tension(value, minimum=0.34)
            if nearest_tension is not None:
                nearest_tension.text = value
            else:
                self.tensions.append(InnerTension(value))
            return

        if self._looks_closed(value):
            nearest = self._nearest_alive(value, minimum=0.18)
            if nearest is not None:
                nearest.alive = False
            return
        if not self._looks_unfinished(value):
            return
        nearest = self._nearest_alive(value, minimum=0.40)
        if nearest is not None:
            nearest.text = value
            return
        self.concerns.append(LingeringConcern(value))

    def _familiar_item(self, text: str) -> Optional[FamiliarExperience]:
        key = _normalized(text)
        for item in self.familiar:
            if _normalized(item.text) == key:
                return item
        return None

    @staticmethod
    def _cue_matches(cue: str, experience: str) -> bool:
        cue_words = _tokens(cue)
        event_words = _tokens(experience)
        if not cue_words or not event_words:
            return False
        overlap = len(cue_words & event_words)
        if len(cue_words) <= 2:
            return overlap == len(cue_words)
        return overlap >= 2

    def process_experience(self, text: str, provenance: str) -> list[str]:
        value = text.strip()
        if not value:
            return []

        for intention in self.intentions:
            if not intention.active and self._cue_matches(intention.cue, value):
                intention.active = True

        if provenance != "body":
            return [value]
        item = self._familiar_item(value)
        if item is None:
            self.familiar.append(FamiliarExperience(value, 1))
            return [value]
        item.repetitions += 1
        if item.repetitions <= 2:
            return [value]
        return []

    def familiar_experiences(self) -> list[str]:
        return [item.text for item in self.familiar if item.repetitions >= 2]

    def pending_intentions(self) -> list[str]:
        return [intention.text for intention in self.intentions if not intention.active]

    def active_intentions(self) -> list[str]:
        return [intention.text for intention in self.intentions if intention.active]

    def observe_memory(self, text: str) -> None:
        return None

    def advance(self, seconds: float, rng: object = None) -> list[str]:
        self.returning_text = ""
        if self.recurrence_refractory:
            self.recurrence_refractory = False
            return []
        if rng is None or seconds <= 0:
            return []

        candidates = self.alive_concerns() + self.alive_tensions()
        if not candidates:
            return []

        # Time supplies only an opportunity for something unresolved to recur. There is
        # no hidden psychological score or deterministic recurrence interval.
        chance = min(0.35, max(0.0, float(seconds)) / 7200.0)
        if rng.random() >= chance:
            return []
        index = min(len(candidates) - 1, int(rng.random() * len(candidates)))
        self.returning_text = candidates[index]
        self.recurrence_refractory = True
        return [self.returning_text]

    def alive_concerns(self) -> list[str]:
        return [concern.text for concern in self.concerns if concern.alive]

    def alive_tensions(self) -> list[str]:
        return [tension.text for tension in self.tensions if tension.alive]

    def _foreground_entries(self, limit: int) -> list[tuple[str, str]]:
        maximum = max(0, int(limit))
        if maximum == 0:
            return []

        entries: list[tuple[str, str]] = []
        seen: set[str] = set()

        def add(kind: str, text: str) -> None:
            value = text.strip()
            key = _normalized(value)
            if not value or key in seen or len(entries) >= maximum:
                return
            seen.add(key)
            entries.append((kind, value))

        if self.returning_text:
            add("returning", self.returning_text)
        for text in reversed(self.active_intentions()):
            add("intention", text)
        for text in reversed(self.alive_tensions()):
            add("tension", text)
        for text in reversed(self.alive_concerns()):
            add("concern", text)
        return entries

    def render_private_context(self, limit: int = 3) -> str:
        entries = self._foreground_entries(limit)
        if not entries:
            return ""

        only_one_concern = (
            len(entries) == 1
            and entries[0][0] == "concern"
            and len(self.alive_concerns()) == 1
        )
        parts: list[str] = []
        for kind, text in entries:
            if kind == "returning":
                parts.append(
                    f"Without my deciding to, my mind has drifted back to this: {text}"
                )
            elif kind == "intention":
                parts.append(
                    f"Something in what just happened brings back something I meant to do: {text}"
                )
            elif kind == "tension":
                parts.append(
                    f"I can still feel both sides of this without forcing a decision: {text}"
                )
            elif only_one_concern:
                parts.append(
                    "Something is still quietly unresolved for me. I do not have to think "
                    f"about it right now, but I am still carrying this: {text}"
                )
            else:
                parts.append(f"This is still somewhere in the back of my mind: {text}")
        return "\n\n".join(parts)
