import tempfile
import unittest
from pathlib import Path

from subjective_loop import CharacterLoop, ScriptedBackend, PRETORIUS_IDENTITY


class LoopTests(unittest.TestCase):
    def make_loop(self, seed=1):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        db = Path(td.name) / "test.sqlite3"
        loop = CharacterLoop(PRETORIUS_IDENTITY, ScriptedBackend(), db, seed=seed, min_thoughts=2, max_thoughts=2)
        return loop, db

    def test_heard_speech_becomes_first_person_experience(self):
        loop, _ = self.make_loop()
        loop.hear("Jay", "Good morning.")
        text = "\n".join(loop.journal.recent_character_text())
        self.assertIn('I hear Jay say, "Good morning."', text)
        self.assertNotIn('Jay said: "Good morning."', text)

    def test_hidden_numeric_state_does_not_enter_awareness(self):
        loop, _ = self.make_loop()
        loop.set_hidden("hunger", 87.321)
        prompt = loop._awareness_prompt()
        self.assertNotIn("87.321", prompt)
        self.assertIn("I'm starving", prompt)

    def test_directional_improvement_is_rendered_as_relief(self):
        loop, _ = self.make_loop()
        loop.set_hidden("hunger", 90)
        loop.set_hidden("hunger", 30)
        text = "\n".join(loop.journal.recent_character_text())
        self.assertIn("My hunger is easing.", text)

    def test_multiple_private_thoughts_are_persisted(self):
        loop, _ = self.make_loop()
        thoughts = loop.think_chain(3)
        self.assertEqual(3, len(thoughts))
        persisted = [kind for _id, kind, _text in loop.journal.dump() if kind == "thought"]
        self.assertEqual(3, len(persisted))

    def test_deliberate_speech_reenters_as_self_experience(self):
        loop, _ = self.make_loop()
        loop.hear("Jay", "What are you working on?")
        text = "\n".join(loop.journal.recent_character_text())
        self.assertIn("I hear myself say", text)

    def test_scripted_backend_exercises_silence_on_second_cycle(self):
        loop, _ = self.make_loop()
        loop.cycle("one")
        spoken_before = len([1 for _id, kind, _text in loop.journal.dump() if kind == "spoken"])
        loop.cycle("two")
        spoken_after = len([1 for _id, kind, _text in loop.journal.dump() if kind == "spoken"])
        self.assertEqual(spoken_before, spoken_after)

    def test_idle_steps_continue_thought_without_user_input(self):
        loop, _ = self.make_loop()
        loop.run_steps(2, 30)
        thoughts = [1 for _id, kind, _text in loop.journal.dump() if kind == "thought"]
        self.assertGreaterEqual(len(thoughts), 4)

    def test_hidden_state_persists_restart(self):
        loop, db = self.make_loop()
        loop.set_hidden("interest", 91)
        second = CharacterLoop(PRETORIUS_IDENTITY, ScriptedBackend(), db, seed=1)
        self.assertEqual(91, second.state.interest)

    def test_malformed_private_narration_is_rejected(self):
        loop, _ = self.make_loop()
        self.assertFalse(loop._valid_private("A moment of confusion as Pretorius considers the problem."))
        self.assertTrue(loop._valid_private("I need to think about this differently."))

    def test_private_copy_is_rejected_as_speech(self):
        loop, _ = self.make_loop()
        private = "I need to think about this differently because the assumption may be wrong."
        self.assertFalse(loop._valid_spoken(private, private))


if __name__ == "__main__":
    unittest.main()
