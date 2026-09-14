from pathlib import Path

path = Path("loopcore.py")
text = path.read_text(encoding="utf-8")

old_import = '''from guardrails import (
    private_copy_match,
    private_narration_reject_reason,
    provenance_reject_reason,
)
'''
new_import = '''from guardrails import (
    action_shape_reject_reason,
    private_copy_match,
    private_narration_reject_reason,
    provenance_reject_reason,
    speech_shape_reject_reason,
)
'''
if old_import not in text and new_import not in text:
    raise SystemExit("cycle3 import anchor not found")
text = text.replace(old_import, new_import, 1)

old_speech = '''        if self._speech_narration.match(value):
            self.journal.developer("speech_rejected_shape", f"text={value}")
            return ""
'''
new_speech = '''        shape_reason = speech_shape_reject_reason(value)
        if shape_reason:
            self.journal.developer(
                "speech_rejected_shape",
                f"reason={shape_reason}; text={value}",
            )
            return ""
'''
if old_speech not in text and new_speech not in text:
    raise SystemExit("cycle3 speech anchor not found")
text = text.replace(old_speech, new_speech, 1)

old_action = '''        if self._mental_action.match(value):
            return "nonphysical_mental_content"
        return self.ingress.reject_reason("action", value)
'''
new_action = '''        shape_reason = action_shape_reject_reason(value)
        if shape_reason:
            return shape_reason
        return self.ingress.reject_reason("action", value)
'''
if old_action not in text and new_action not in text:
    raise SystemExit("cycle3 action anchor not found")
text = text.replace(old_action, new_action, 1)

path.write_text(text, encoding="utf-8")
