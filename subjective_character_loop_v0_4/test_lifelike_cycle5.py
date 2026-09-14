import tempfile
import unittest
from pathlib import Path

from lifelike import FirstPersonLife
from subjective_loop import CharacterLoop, PRETORIUS_IDENTITY
from test_support import RecordingBackend


class LifelikeCycle5Tests(unittest.TestCase):
    def test_unfinished_concern_survives_release_and_restart(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "loop.sqlite3"
            backend = RecordingBackend(
                private=["I still do not know why Jay changed the subject when I asked about Henry."],
                initiation=["THINK"],
                probes=["RELEASE"],
                speech=[""],
            )
            first = CharacterLoop(PRETORIUS_IDENTITY, backend, path, seed=1)
            first.cognitive_cycle("test")
            first.journal.conn.close()

            second_backend = RecordingBackend(initiation=["REST"], speech=[""])
            second = CharacterLoop(PRETORIUS_IDENTITY, second_backend, path, seed=1)
            self.addCleanup(second.journal.conn.close)
            prompt = second._initiation_prompt()
            self.assertIn("Jay changed the subject", prompt)
            self.assertIn("still quietly unresolved", prompt)

    def test_repetition_does_not_multiply_same_concern(self):
        life = FirstPersonLife()
        life.observe_thought("I still do not know why Henry left so abruptly.")
        life.observe_thought("I still do not know why Henry left so abruptly.")
        life.observe_thought("I keep coming back to why Henry left so abruptly.")
        self.assertEqual(len(life.alive_concerns()), 1)

    def test_explicit_resolution_retires_related_concern(self):
        life = FirstPersonLife()
        life.observe_thought("I still do not know why Henry left so abruptly.")
        life.observe_thought("I understand now why Henry left so abruptly. That settles it.")
        self.assertEqual(life.alive_concerns(), [])

    def test_private_context_is_character_language_not_telemetry(self):
        life = FirstPersonLife()
        life.observe_thought("I wonder whether I should apologize to Jay later.")
        rendered = life.render_private_context()
        low = rendered.lower()
        self.assertIn("i wonder whether", low)
        self.assertNotIn("score", low)
        self.assertNotIn("priority", low)
        self.assertNotIn("activation", low)
        self.assertNotIn("thread id", low)

    def test_quiet_turn_does_not_erase_unfinished_life(self):
        life = FirstPersonLife()
        life.observe_thought("I am not ready to decide what I think about that yet.")
        before = life.render_private_context()
        self.assertEqual(life.advance(900.0), [])
        self.assertEqual(before, life.render_private_context())


if __name__ == "__main__":
    unittest.main()
