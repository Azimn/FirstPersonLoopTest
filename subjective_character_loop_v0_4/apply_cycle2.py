from pathlib import Path

path = Path("loopcore.py")
text = path.read_text(encoding="utf-8")

old_import = "from guardrails import private_narration_reject_reason, provenance_reject_reason\n"
new_import = '''from guardrails import (
    private_copy_match,
    private_narration_reject_reason,
    provenance_reject_reason,
)
'''
if old_import not in text and new_import not in text:
    raise SystemExit("cycle2 import anchor not found")
text = text.replace(old_import, new_import, 1)

old_matcher = '''            seen: set[str] = set()
            for thought in candidates:
                normalized_thought = " ".join(thought.split())
                if not normalized_thought or normalized_thought in seen:
                    continue
                seen.add(normalized_thought)
                if normalized_spoken == normalized_thought:
                    self.journal.developer(
                        "speech_rejected_private_copy",
                        "ratio=1.000; source=recent_private",
                    )
                    return ""
                if len(normalized_thought) >= 40:
                    ratio = difflib.SequenceMatcher(
                        None,
                        normalized_spoken,
                        normalized_thought,
                    ).ratio()
                    if ratio >= 0.88:
                        self.journal.developer(
                            "speech_rejected_private_copy",
                            f"ratio={ratio:.3f}; source=recent_private",
                        )
                        return ""
'''
new_matcher = '''            seen: set[str] = set()
            for thought in candidates:
                normalized_thought = " ".join(thought.split())
                if not normalized_thought or normalized_thought in seen:
                    continue
                seen.add(normalized_thought)
                matched, detail = private_copy_match(value, normalized_thought)
                if matched:
                    self.journal.developer(
                        "speech_rejected_private_copy",
                        f"{detail}; source=recent_private",
                    )
                    return ""
'''
if old_matcher not in text and new_matcher not in text:
    raise SystemExit("cycle2 matcher anchor not found")
text = text.replace(old_matcher, new_matcher, 1)

path.write_text(text, encoding="utf-8")
