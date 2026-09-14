from __future__ import annotations

import difflib
import re
from typing import Optional


_ALLOWED_PROVENANCE: dict[str, frozenset[str]] = {
    "thought": frozenset({"private"}),
    "memory": frozenset({"memory"}),
    "experience": frozenset(
        {
            "runtime_experience",
            "external_speech",
            "opaque_action",
            "body",
            "action",
            "self_speech",
        }
    ),
}

_PRIVATE_OUTSIDE_NARRATION = re.compile(
    r"^\s*(?:"
    r"a\s+moment\s+of\b|"
    r"(?:dr\.\s+)?pretorius\b|"
    r"kiki\b|"
    r"the\s+character\b|"
    r"(?:he|she)\s+(?:thinks?|feels?)\b"
    r")",
    re.IGNORECASE,
)


def provenance_reject_reason(kind: str, provenance: str) -> Optional[str]:
    allowed = _ALLOWED_PROVENANCE.get(kind)
    if allowed is None:
        return "unknown_awareness_kind"
    if provenance not in allowed:
        return "invalid_provenance"
    return None


def private_narration_reject_reason(text: str) -> Optional[str]:
    value = text.strip()
    if value.startswith(("[", "(", "*")):
        return "outside_narration"
    if _PRIVATE_OUTSIDE_NARRATION.match(value):
        return "outside_narration"
    return None


def private_copy_match(spoken: str, private_text: str) -> tuple[bool, str]:
    """Cycle-1 compatibility matcher. Later review cycles harden span leakage."""
    normalized_spoken = " ".join(spoken.split())
    normalized_private = " ".join(private_text.split())
    if not normalized_private:
        return False, ""
    if normalized_spoken == normalized_private:
        return True, "ratio=1.000"
    if len(normalized_private) >= 40:
        ratio = difflib.SequenceMatcher(None, normalized_spoken, normalized_private).ratio()
        if ratio >= 0.88:
            return True, f"ratio={ratio:.3f}"
    return False, ""


def speech_shape_reject_reason(text: str) -> Optional[str]:
    value = text.strip()
    if re.match(
        r"^\s*(?:(?:dr\.\s+)?pretorius|kiki|the character|he|she)\s+"
        r"(?:says?|speaks?|replies?|answers?)\b",
        value,
        re.IGNORECASE,
    ):
        return "third_person_speech_narration"
    return None


def action_shape_reject_reason(text: str) -> Optional[str]:
    value = text.strip()
    if re.match(
        r"^\s*I\s+(?:think|wonder|remember|believe|suspect|realize|consider|imagine|"
        r"hope|fear|know|understand)\b",
        value,
        re.IGNORECASE,
    ):
        return "nonphysical_mental_content"
    return None
