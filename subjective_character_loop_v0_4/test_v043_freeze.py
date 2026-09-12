import tempfile
import unittest
from pathlib import Path

from subjective_loop import CharacterLoop, PRETORIUS_IDENTITY
from test_support import LoopTestCase, RecordingBackend


class V043FreezeTests(LoopTestCase):
    def test_behavior_receives_complete_current_thought_episode(self):
        first = "I see the decisive premise now: the vessel is not the identity."
        second = "That is enough for the moment; I can leave the implication there."
        backend = RecordingBackend(
            private=[first, second],
            initiation=["THINK"],
            probes=["CONTINUE", "RELEASE"],
            speech=[""],
        )
        loop, _ = self.make_loop(backend)
        self.assertEqual(loop.cognitive_cycle("test"), [first, second])
        speech_prompt = [
            user for system, user, _, _ in backend.calls
            if "say anything aloud" in system.lower()
        ][0]
        self.assertIn(first, speech_prompt)
        self.assertIn(second, speech_prompt)
        self.assertIn("CURRENT PRIVATE THOUGHT EPISODE", speech_prompt)

    def test_action_context_is_rebuilt_after_speech_and_self_hearing(self):
        backend = RecordingBackend(
            initiation=["REST"],
            speech=["Good morning, Jay."],
            actions=["I nod once."],
        )
        loop, _ = self.make_loop(backend, allow_movement=True)
        loop.hear("Jay", "Good morning.")
        action_prompt = [
            user for system, user, _, _ in backend.calls
            if "physical action" in system.lower()
        ][0]
        self.assertIn('I hear myself say, "Good morning, Jay."', action_prompt)
        self.assertIn("I hear Jay say:\n> Good morning.", action_prompt)

    def test_behavior_freshness_watermark_survives_restart(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "loop.sqlite3"
            first_backend = RecordingBackend()
            first = CharacterLoop(PRETORIUS_IDENTITY, first_backend, path, seed=1)
            first.hear("Jay", "The bell just rang.", think=False)
            first.journal.conn.close()

            second_backend = RecordingBackend(initiation=["REST"], speech=[""])
            second = CharacterLoop(PRETORIUS_IDENTITY, second_backend, path, seed=1)
            self.addCleanup(second.journal.conn.close)
            second.cognitive_cycle("time")
            speech_prompt = [
                user for system, user, _, _ in second_backend.calls
                if "say anything aloud" in system.lower()
            ][0]
            new_section = speech_prompt.split(
                "NEW FIRST-PERSON EXPERIENCE SINCE THE PREVIOUS BEHAVIOR OPPORTUNITY:", 1
            )[1].split("CURRENT PRIVATE THOUGHT EPISODE", 1)[0]
            self.assertIn("The bell just rang.", new_section)

    def test_behavior_prompt_does_not_expose_raw_runtime_trigger(self):
        backend = RecordingBackend(initiation=["REST"], speech=[""])
        loop, _ = self.make_loop(backend)
        loop.cognitive_cycle("secret_runtime_trigger")
        speech_prompt = [
            user for system, user, _, _ in backend.calls
            if "say anything aloud" in system.lower()
        ][0]
        self.assertNotIn("secret_runtime_trigger", speech_prompt)
        self.assertNotIn("CURRENT OPPORTUNITY", speech_prompt)


if __name__ == "__main__":
    unittest.main()
