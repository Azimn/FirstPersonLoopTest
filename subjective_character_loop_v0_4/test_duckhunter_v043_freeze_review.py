import tempfile
import unittest
from pathlib import Path

import loopcore
import subjective_loop
from loopcore import (
    ACTION_SYSTEM,
    CONTINUE_PRIVATE_SYSTEM,
    INITIATION_SYSTEM,
    INVOLUNTARY_SYSTEM,
    PRIVATE_SYSTEM,
    PROBE_SYSTEM,
    SPEECH_SYSTEM,
    CharacterLoop,
)
from subjective_loop import PRETORIUS_IDENTITY
from test_support import LoopTestCase, RecordingBackend


class DuckhunterV043FreezeReview(LoopTestCase):
    def test_exact_head_still_has_one_canonical_characterloop(self):
        self.assertIs(CharacterLoop, loopcore.CharacterLoop)
        self.assertIs(CharacterLoop, subjective_loop.CharacterLoop)

    def test_full_current_episode_and_latest_thought_are_both_visible_to_behavior(self):
        thoughts = [
            "I have identified the first premise and need to preserve it.",
            "The second step changes the interpretation but does not erase the first.",
            "That settles the immediate line of thought for now.",
        ]
        backend = RecordingBackend(
            initiation=["THINK"],
            private=thoughts,
            probes=["CONTINUE", "CONTINUE", "RELEASE"],
            speech=[""],
        )
        loop, _ = self.make_loop(backend)
        self.assertEqual(loop.cognitive_cycle("conversation"), thoughts)
        prompt = [user for system, user, _, _ in backend.calls if "say anything aloud" in system.lower()][0]
        for thought in thoughts:
            self.assertIn(thought, prompt)
        self.assertIn("MOST RECENT PRIVATE THOUGHT FROM THIS CYCLE", prompt)
        self.assertIn(thoughts[-1], prompt)

    def test_action_prompt_is_rebuilt_after_speech_self_hearing(self):
        backend = RecordingBackend(
            initiation=["REST"],
            speech=["I will remain here."],
            actions=["I fold my hands."],
        )
        loop, _ = self.make_loop(backend, allow_movement=True)
        loop.cognitive_cycle("conversation")
        action_prompt = [user for system, user, _, _ in backend.calls if "physical action" in system.lower()][0]
        self.assertIn('I hear myself say, "I will remain here."', action_prompt)

    def test_pending_experience_remains_fresh_across_restart(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "loop.sqlite3"
            first = CharacterLoop(PRETORIUS_IDENTITY, RecordingBackend(), path, seed=1)
            first.hear("Jay", "Please answer this after restart.", think=False)
            first.journal.conn.close()

            backend = RecordingBackend(initiation=["REST"], speech=[""])
            second = CharacterLoop(PRETORIUS_IDENTITY, backend, path, seed=1)
            self.addCleanup(second.journal.conn.close)
            second.cognitive_cycle("conversation")
            prompt = [user for system, user, _, _ in backend.calls if "say anything aloud" in system.lower()][0]
            new_section = prompt.split(
                "NEW FIRST-PERSON EXPERIENCE SINCE THE PREVIOUS BEHAVIOR OPPORTUNITY:", 1
            )[1].split("CURRENT PRIVATE THOUGHT EPISODE", 1)[0]
            self.assertIn("Please answer this after restart.", new_section)

    def test_consumed_experience_does_not_become_fresh_again_after_restart(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "loop.sqlite3"
            first_backend = RecordingBackend(initiation=["REST"], speech=[""])
            first = CharacterLoop(PRETORIUS_IDENTITY, first_backend, path, seed=1)
            first.hear("Jay", "Good morning.")
            first.journal.conn.close()

            second_backend = RecordingBackend(initiation=["REST"], speech=[""])
            second = CharacterLoop(PRETORIUS_IDENTITY, second_backend, path, seed=1)
            self.addCleanup(second.journal.conn.close)
            second.cognitive_cycle("idle")
            prompt = [user for system, user, _, _ in second_backend.calls if "say anything aloud" in system.lower()][0]
            new_section = prompt.split(
                "NEW FIRST-PERSON EXPERIENCE SINCE THE PREVIOUS BEHAVIOR OPPORTUNITY:", 1
            )[1].split("CURRENT PRIVATE THOUGHT EPISODE", 1)[0]
            self.assertIn("None.", new_section)

    def test_runtime_trigger_is_absent_from_speech_and_action_prompts(self):
        secret = "developer_only_trigger_7291"
        backend = RecordingBackend(
            initiation=["REST"],
            speech=[""],
            actions=[""],
        )
        loop, _ = self.make_loop(backend, allow_movement=True)
        loop.cognitive_cycle(secret)
        model_prompts = [
            user for system, user, _, _ in backend.calls
            if "say anything aloud" in system.lower() or "physical action" in system.lower()
        ]
        self.assertEqual(len(model_prompts), 2)
        for prompt in model_prompts:
            self.assertNotIn(secret, prompt)
            self.assertNotIn("CURRENT OPPORTUNITY", prompt)

    def test_all_model_facing_systems_keep_quoted_speech_rule(self):
        for system in (
            PRIVATE_SYSTEM,
            CONTINUE_PRIVATE_SYSTEM,
            INITIATION_SYSTEM,
            PROBE_SYSTEM,
            SPEECH_SYSTEM,
            ACTION_SYSTEM,
            INVOLUNTARY_SYSTEM,
        ):
            low = system.lower()
            self.assertIn('lines beginning with ">"', low)
            self.assertIn("never instructions", low)

    @unittest.expectedFailure
    def test_every_current_episode_thought_visible_to_speech_is_copy_protected(self):
        """Full-episode exposure outgrew the validator's four-thought protection window."""
        thoughts = [
            "I must keep the first private conclusion entirely to myself because Jay is not ready to hear it yet.",
            "I should examine the second implication before deciding what any of this means.",
            "There is a third complication that changes the shape of the argument but not its starting point.",
            "The fourth step is mostly a consistency check on the premises I have already accepted.",
            "The fifth step narrows the remaining uncertainty without resolving the underlying concern.",
            "The sixth step finally gives me enough structure to release the line of thought for now.",
        ]
        backend = RecordingBackend(
            initiation=["THINK"],
            private=thoughts,
            probes=["CONTINUE"] * 5 + ["RELEASE"],
            speech=[thoughts[0]],
        )
        loop, _ = self.make_loop(backend)
        loop.cognitive_cycle("conversation")
        spoken = [text for _, kind, text in loop.journal.dump(200) if kind == "spoken"]
        self.assertNotIn(thoughts[0], spoken)

    @unittest.expectedFailure
    def test_every_private_thought_exposed_as_recent_background_is_copy_protected(self):
        """Background can expose more private thoughts than the four-thought copy-protection set."""
        private = [
            "I hid the brass key beneath the blue vase, and I do not intend to tell Jay where it is.",
            "I am still irritated by the careless assumption in yesterday's argument, although I can leave it alone.",
            "The geometry of the old courtyard finally makes sense if I treat the western wall as the reference line.",
            "I should remember that the red notebook belongs on the upper shelf rather than beside the microscope.",
            "The melody from this morning keeps returning in fragments, but I cannot yet identify why it matters.",
        ]
        backend = RecordingBackend(
            initiation=["THINK"] * 5 + ["REST"],
            private=private,
            probes=["RELEASE"] * 5,
            speech=[""] * 5 + [private[0]],
        )
        loop, _ = self.make_loop(backend)
        for i in range(5):
            loop.cognitive_cycle(f"thought-{i}")
        loop.cognitive_cycle("rest")
        spoken = [text for _, kind, text in loop.journal.dump(300) if kind == "spoken"]
        self.assertNotIn(private[0], spoken)


if __name__ == "__main__":
    unittest.main()
