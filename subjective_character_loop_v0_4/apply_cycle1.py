from pathlib import Path

path = Path("loopcore.py")
text = path.read_text(encoding="utf-8")

old_import = "from backends import ModelBackend\nfrom experience import ExperienceCompiler, HiddenState\n"
new_import = (
    "from backends import ModelBackend\n"
    "from experience import ExperienceCompiler, HiddenState\n"
    "from guardrails import private_narration_reject_reason, provenance_reject_reason\n"
)
if old_import not in text and new_import not in text:
    raise SystemExit("cycle1 import anchor not found")
text = text.replace(old_import, new_import, 1)

old_private = '''        if provenance == "private":
            if value.startswith(("[", "(", "*")):
                return "outside_narration"
            if low.startswith(("a moment of ", "pretorius ", "dr. pretorius ", "kiki ")):
                return "outside_narration"
            if any(term in low for term in self._outside_narration):
                return "outside_narration"
        return None
'''
new_private = '''        if provenance == "private":
            reason = private_narration_reject_reason(value)
            if reason:
                return reason
        return None
'''
if old_private not in text and new_private not in text:
    raise SystemExit("cycle1 private narration anchor not found")
text = text.replace(old_private, new_private, 1)

old_subjective = '''    def add_subjective(self, kind: str, text: str, provenance: str) -> bool:
        if kind not in self._awareness_kinds:
            raise ValueError(f"Not an awareness-bearing journal kind: {kind}")
        value = text.strip()
        reason = self.ingress.reject_reason(provenance, value)
'''
new_subjective = '''    def add_subjective(self, kind: str, text: str, provenance: str) -> bool:
        if kind not in self._awareness_kinds:
            raise ValueError(f"Not an awareness-bearing journal kind: {kind}")
        value = text.strip()
        reason = provenance_reject_reason(kind, provenance)
        if reason:
            self.developer(
                "ingress_rejected",
                f"provenance={provenance}; reason={reason}; text={value}",
            )
            return False
        reason = self.ingress.reject_reason(provenance, value)
'''
if old_subjective not in text and new_subjective not in text:
    raise SystemExit("cycle1 subjective ingress anchor not found")
text = text.replace(old_subjective, new_subjective, 1)

path.write_text(text, encoding="utf-8")
