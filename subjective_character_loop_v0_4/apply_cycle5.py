from pathlib import Path
import re

path = Path("loopcore.py")
text = path.read_text(encoding="utf-8")

# Clean accumulated duplicate guardrail imports and install one canonical import block.
start = text.index("from backends import ModelBackend")
marker = text.index("\n\n_QUOTED_SPEECH_RULE", start)
imports = '''from backends import ModelBackend
from experience import ExperienceCompiler, HiddenState
from guardrails import (
    action_shape_reject_reason,
    private_copy_match,
    private_narration_reject_reason,
    provenance_reject_reason,
    speech_shape_reject_reason,
)
from lifelike import FirstPersonLife'''
text = text[:start] + imports + text[marker:]

old = '''        self.compiler = ExperienceCompiler(self.rng, saved_compiler)
        if saved_compiler is None:
            self.compiler.prime(self.state)

        self.allow_movement = allow_movement'''
new = '''        self.compiler = ExperienceCompiler(self.rng, saved_compiler)
        if saved_compiler is None:
            self.compiler.prime(self.state)
        self.life = FirstPersonLife.from_json(
            self.journal.load_json("first_person_life")
        )

        self.allow_movement = allow_movement'''
assert old in text
text = text.replace(old, new, 1)

old = '''        self.journal.save_json(
            "behavior_seen_episode_id",
            int(self._behavior_seen_episode_id),
        )

    def _awareness_prompt'''
new = '''        self.journal.save_json(
            "behavior_seen_episode_id",
            int(self._behavior_seen_episode_id),
        )
        self.journal.save_json("first_person_life", self.life.to_json())

    def _awareness_prompt'''
assert old in text
text = text.replace(old, new, 1)

old = '''        awareness = "\\n\\n".join(recent) if recent else "I am here with my own thoughts."
        return (
            f"This is who I understand myself to be:\\n{self.identity}\\n\\n"
            f"This is what is currently available in my awareness:\\n{awareness}"
        )'''
new = '''        awareness = "\\n\\n".join(recent) if recent else "I am here with my own thoughts."
        carried = self.life.render_private_context()
        if carried:
            awareness = f"{awareness}\\n\\n{carried}"
        return (
            f"This is who I understand myself to be:\\n{self.identity}\\n\\n"
            f"This is what is currently available in my awareness:\\n{awareness}"
        )'''
assert old in text
text = text.replace(old, new, 1)

old = '''    def _append_experience(self, text: str, provenance: str = "runtime_experience") -> bool:
        value = text.strip()
        if not value or not self._accept_subjective("experience", value, provenance):
            return False
        print(f"  experience: {value}")
        return True'''
new = '''    def _append_experience(self, text: str, provenance: str = "runtime_experience") -> bool:
        value = text.strip()
        if not value:
            return False
        accepted = False
        for subjective in self.life.process_experience(value, provenance):
            subjective = subjective.strip()
            if subjective and self._accept_subjective("experience", subjective, provenance):
                print(f"  experience: {subjective}")
                accepted = True
        return accepted'''
assert old in text
text = text.replace(old, new, 1)

old = '''        if self._accept_subjective("memory", text, "memory"):
            print(f"  memory:     {text}")
            self._save_runtime()'''
new = '''        if self._accept_subjective("memory", text, "memory"):
            self.life.observe_memory(text)
            print(f"  memory:     {text}")
            self._save_runtime()'''
assert old in text
text = text.replace(old, new, 1)

old = '''            if text and self._accept_subjective("thought", text, "private"):
                print(f"  thought:    {text}")
                return text'''
new = '''            if text and self._accept_subjective("thought", text, "private"):
                self.life.observe_thought(text)
                print(f"  thought:    {text}")
                return text'''
assert old in text
text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
