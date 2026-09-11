import tempfile
import unittest
from pathlib import Path

from subjective_loop import CharacterLoop, ScriptedBackend, PRETORIUS_IDENTITY


class SubjectiveLoopTests(unittest.TestCase):
    def make_loop(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        db = Path(temp.name) / "test.sqlite3"
        return CharacterLoop(PRETORIUS_IDENTITY, ScriptedBackend(), db, seed=3)

    def test_hidden_values_do_not_appear_in_character_journal(self):
        loop = self.make_loop()
        loop.set_hidden("hunger", 87.321)
        text = "\n".join(loop.journal.recent_character_text(50))
        self.assertNotIn("87.321", text)
        self.assertNotIn("hunger =", text.lower())
        self.assertIn("starving", text.lower())

    def test_heard_speech_becomes_first_person_experience(self):
        loop = self.make_loop()
        loop.hear("Sarah", "I never promised that.")
        text = "\n".join(loop.journal.recent_character_text(50))
        self.assertIn('I hear Sarah say, "I never promised that."', text)

    def test_interest_has_positive_first_person_injection(self):
        loop = self.make_loop()
        loop.set_interest(90, "a new method for creating synthetic life")
        text = "\n".join(loop.journal.recent_character_text(50))
        self.assertIn("I can't stop thinking about", text)
        self.assertIn("synthetic life", text)

    def test_speech_is_persisted_separately_from_private_thought(self):
        loop = self.make_loop()
        loop.cycle()
        rows = loop.journal.dump(50)
        kinds = [kind for _id, kind, _text in rows]
        self.assertIn("thought", kinds)
        # Scripted backend deliberately chooses silence for intentional speech.
        self.assertNotIn("spoken", kinds)

    def test_restart_preserves_hidden_state_and_history(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        db = Path(temp.name) / "persist.sqlite3"
        first = CharacterLoop(PRETORIUS_IDENTITY, ScriptedBackend(), db, seed=1)
        first.set_hidden("fatigue", 70)
        first.inject_experience("I keep thinking about the unfinished experiment.")
        second = CharacterLoop(PRETORIUS_IDENTITY, ScriptedBackend(), db, seed=1)
        self.assertGreaterEqual(second.state.fatigue, 70)
        text = "\n".join(second.journal.recent_character_text(50))
        self.assertIn("unfinished experiment", text)


if __name__ == "__main__":
    unittest.main()
