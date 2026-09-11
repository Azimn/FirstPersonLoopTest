import tempfile
import unittest
from pathlib import Path

from subjective_loop import (
    ACTION_SYSTEM,
    INVOLUNTARY_SYSTEM,
    PRETORIUS_IDENTITY,
    PRIVATE_SYSTEM,
    SPEECH_SYSTEM,
    CharacterLoop,
    ScriptedBackend,
)


class CaptureBackend:
    def __init__(self):
        self.calls = []

    def complete(self, system: str, user: str, temperature: float = 0.8) -> str:
        self.calls.append((system, user, temperature))
        if system == PRIVATE_SYSTEM:
            return "I am considering what I just heard."
        if system == SPEECH_SYSTEM:
            return "I heard you."
        if system == ACTION_SYSTEM:
            return "I turn toward the sound."
        if system == INVOLUNTARY_SYSTEM:
            return "Ah!"
        return ""


class DuckhunterAdversarialTests(unittest.TestCase):
    def make_loop(self, backend=None, *, movement=False, seed=3):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        db = Path(temp.name) / "test.sqlite3"
        loop = CharacterLoop(
            PRETORIUS_IDENTITY,
            backend or ScriptedBackend(),
            db,
            seed=seed,
            allow_movement=movement,
        )
        return loop, db

    def test_cycle_preserves_private_then_public_order(self):
        backend = CaptureBackend()
        loop, _ = self.make_loop(backend)
        loop.hear("Jay", "Good morning. What are you working on currently?")
        systems = [row[0] for row in backend.calls]
        self.assertGreaterEqual(len(systems), 2)
        self.assertEqual(systems[0], PRIVATE_SYSTEM)
        self.assertEqual(systems[1], SPEECH_SYSTEM)
        speech_prompt = backend.calls[1][1]
        self.assertIn("I am considering what I just heard.", speech_prompt)

    def test_heard_speech_reaches_backend_only_as_first_person_experience(self):
        backend = CaptureBackend()
        loop, _ = self.make_loop(backend)
        loop.hear("Jay", "Good morning.")
        first_prompt = backend.calls[0][1]
        self.assertIn('I hear Jay say, "Good morning."', first_prompt)
        self.assertNotIn('Jay said: "Good morning."', first_prompt)

    def test_private_thought_is_not_public_journal_content(self):
        backend = CaptureBackend()
        loop, _ = self.make_loop(backend)
        loop.hear("Jay", "Hello.")
        public = "\n".join(loop.journal.recent_public_text(20))
        self.assertNotIn("I am considering what I just heard.", public)
        self.assertIn("I heard you.", public)

    def test_spoken_output_becomes_self_experience(self):
        backend = CaptureBackend()
        loop, _ = self.make_loop(backend)
        loop.hear("Jay", "Hello.")
        character_text = "\n".join(loop.journal.recent_character_text(30))
        self.assertIn('I hear myself say, "I heard you."', character_text)

    def test_movement_is_separate_and_self_perceived(self):
        backend = CaptureBackend()
        loop, _ = self.make_loop(backend, movement=True)
        loop.hear("Jay", "Over here.")
        public = "\n".join(loop.journal.recent_public_text(30))
        character_text = "\n".join(loop.journal.recent_character_text(30))
        self.assertIn("I turn toward the sound.", public)
        self.assertIn("I turn toward the sound.", character_text)

    def test_raw_hidden_numeric_value_never_enters_backend_prompt(self):
        backend = CaptureBackend()
        loop, _ = self.make_loop(backend)
        loop.set_hidden("hunger", 87.321)
        loop.cycle()
        combined = "\n".join(user for _system, user, _temp in backend.calls)
        self.assertNotIn("87.321", combined)
        self.assertNotIn("hunger =", combined.lower())
        self.assertIn("starving", combined.lower())

    @unittest.expectedFailure
    def test_character_access_api_rejects_raw_machine_state(self):
        """The first-person firewall should be enforced, not merely conventional."""
        loop, _ = self.make_loop()
        loop.inject_experience("hunger = 87.321")
        text = "\n".join(loop.journal.recent_character_text(20))
        self.assertNotIn("87.321", text)
        self.assertNotIn("hunger =", text.lower())

    @unittest.expectedFailure
    def test_downward_threshold_crossing_is_experienced_as_relief_not_onset(self):
        """Falling from severe hunger should not sound like hunger is newly worsening."""
        loop, _ = self.make_loop()
        loop.set_hidden("hunger", 90)
        before = len(loop.journal.dump(100))
        loop.set_hidden("hunger", 30)
        new_rows = loop.journal.dump(100)[before:]
        text = "\n".join(row[2] for row in new_rows)
        lowered = text.lower()
        self.assertTrue(
            any(term in lowered for term in ("less hungry", "easing", "relief", "subsiding", "better")),
            text,
        )

    @unittest.expectedFailure
    def test_scripted_conversation_can_produce_public_response(self):
        """Architectural test mode should exercise the complete private-to-public loop."""
        loop, _ = self.make_loop(ScriptedBackend())
        loop.hear("Jay", "Good morning. What are you working on currently?")
        kinds = [kind for _id, kind, _text in loop.journal.dump(100)]
        self.assertIn("thought", kinds)
        self.assertIn("spoken", kinds)

    @unittest.expectedFailure
    def test_loop_has_self_driven_progression_after_input(self):
        """A loop should be able to advance again without another user command."""
        loop, _ = self.make_loop(ScriptedBackend())
        loop.hear("Jay", "Good morning.")
        first_count = len(loop.journal.dump(100))
        # No user input, wait command, or external caller should be required for at
        # least one subsequent internal progression in a continuously running loop.
        second_count = len(loop.journal.dump(100))
        self.assertGreater(second_count, first_count)

    def test_restart_preserves_state_but_does_not_reemit_same_threshold(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        db = Path(temp.name) / "persist.sqlite3"
        first = CharacterLoop(PRETORIUS_IDENTITY, ScriptedBackend(), db, seed=2)
        first.set_hidden("hunger", 90)
        prior_count = len(first.journal.dump(100))
        second = CharacterLoop(PRETORIUS_IDENTITY, ScriptedBackend(), db, seed=2)
        second.cycle()
        rows = second.journal.dump(100)
        repeated_starving = [text for _id, kind, text in rows[prior_count:] if kind == "experience" and "starving" in text.lower()]
        self.assertEqual(repeated_starving, [])


if __name__ == "__main__":
    unittest.main()
