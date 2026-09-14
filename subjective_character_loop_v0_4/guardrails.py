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
_WORD = re.compile(r"[A-Za-z0-9]+(?:['’][A-Za-z0-9]+)?")


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


def _tokens(text: str) -> list[str]:
    return [token.lower().replace("’", "'") for token in _WORD.findall(text)]


def private_copy_match(spoken: str, private_text: str) -> tuple[bool, str]:
    """Reject direct or near-direct copying while still allowing semantic paraphrase."""
    normalized_spoken = " ".join(spoken.split())
    normalized_private = " ".join(private_text.split())
    if not normalized_private:
        return False, ""
    if normalized_spoken == normalized_private:
        return True, "ratio=1.000"

    spoken_tokens = _tokens(spoken)
    private_tokens = _tokens(private_text)
    if not private_tokens:
        return False, ""

    spoken_lexical = " ".join(spoken_tokens)
    private_lexical = " ".join(private_tokens)
    if len(private_tokens) >= 6 and private_lexical in spoken_lexical:
        return True, f"verbatim_span_words={len(private_tokens)}"

    if len(normalized_private) >= 40:
        ratio = difflib.SequenceMatcher(
            None,
            normalized_spoken,
            normalized_private,
            autojunk=False,
        ).ratio()
        if ratio >= 0.88:
            return True, f"ratio={ratio:.3f}"

    matcher = difflib.SequenceMatcher(
        None,
        spoken_tokens,
        private_tokens,
        autojunk=False,
    )
    match = matcher.find_longest_match(
        0,
        len(spoken_tokens),
        0,
        len(private_tokens),
    )
    matched_words = match.size
    if matched_words:
        matched_chars = len(" ".join(private_tokens[match.b : match.b + matched_words]))
        shorter = min(len(spoken_tokens), len(private_tokens))
        coverage = matched_words / shorter if shorter else 0.0
        if matched_words >= 8 and matched_chars >= 45:
            return True, f"verbatim_span_words={matched_words}; coverage={coverage:.3f}"
        if matched_words >= 6 and matched_chars >= 32 and coverage >= 0.75:
            return True, f"verbatim_span_words={matched_words}; coverage={coverage:.3f}"

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
    if re.match(
        r"^\s*I\s+(?:say|reply|answer|speak|tell|ask)\b",
        value,
        re.IGNORECASE,
    ):
        return "first_person_speech_narration"
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
    if re.match(
        r"^\s*(?:I\s+am\b|I'm\b|I\s+feel\b|I\s+want\b|I\s+need\b|I\s+wish\b|"
        r"I\s+intend\b|I\s+plan\b|I\s+decide\b|I\s+prefer\b|I\s+like\b|I\s+dislike\b)",
        value,
        re.IGNORECASE,
    ):
        return "nonphysical_state_or_intent"
    return None
