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


class TwoThoughtBackend(RecordingBackend):
    def __init__(self):
        super().__init__(
            initiation=["THINK"],
            private=[
                "The answer I want to give Jay is violet.",
                "Yes. That settles what I should say.",
            ],
            probes=["CONTINUE", "RELEASE"],
            speech=[""],
        )


class SpeechThenActionBackend(RecordingBackend):
    def __init__(self):
        super().__init__(
            initiation=["REST"],
            speech=["I will stay exactly where I am."],
            actions=["I step toward the door."],
        )


class DuckhunterV042FreezeReview(LoopTestCase):
    def test_exact_freeze_uses_one_canonical_characterloop(self):
        self.assertIs(CharacterLoop, loopcore.CharacterLoop)
        self.assertIs(CharacterLoop, subjective_loop.CharacterLoop)

    def test_awareness_storage_still_requires_typed_provenance(self):
        loop, _ = self.make_loop(RecordingBackend())
        with self.assertRaises(RuntimeError):
            loop.journal.add("thought", "I can see that hunger = 87.321.")
        self.assertNotIn("87.321", self.journal_text(loop))

    def test_recent_private_copy_remains_protected_after_rest(self):
        private = (
            "I do not want to tell Jay yet that I suspect the premise itself is wrong, "
            "because I need to examine it privately first."
        )
        backend = RecordingBackend(
            initiation=["THINK", "REST"],
            private=[private],
            probes=["RELEASE"],
            speech=["", private],
        )
        loop, _ = self.make_loop(backend)
        loop.cognitive_cycle("first")
        loop.cognitive_cycle("idle")
        spoken = [text for _, kind, text in loop.journal.dump(100) if kind == "spoken"]
        self.assertNotIn(private, spoken)

    def test_initiation_prompt_does_not_receive_runtime_trigger(self):
        backend = RecordingBackend(initiation=["REST", "REST"], speech=["", ""])
        loop, _ = self.make_loop(backend)
        loop.cognitive_cycle("conversation")
        first = [user for system, user, _, _ in backend.calls if "thought-initiation" in system.lower()][0]
        loop.cognitive_cycle("idle")
        second = [user for system, user, _, _ in backend.calls if "thought-initiation" in system.lower()][1]
        self.assertNotIn("CURRENT OPPORTUNITY", first)
        self.assertNotIn("CURRENT OPPORTUNITY", second)

    def test_all_model_facing_prompt_systems_mark_quoted_speech_non_instructional(self):
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

    def test_completed_behavior_makes_old_event_background(self):
        class GreetingBackend(RecordingBackend):
            def complete(self, system, user, temperature=0.8, max_tokens=160):
                self.calls.append((system, user, temperature, max_tokens))
                low = system.lower()
                if "thought-initiation" in low:
                    return "REST"
                if "say anything aloud" in low:
                    new = user.split(
                        "NEW FIRST-PERSON EXPERIENCE SINCE THE PREVIOUS BEHAVIOR OPPORTUNITY:", 1
                    )[-1].split("MOST RECENT PRIVATE THOUGHT FROM THIS CYCLE:", 1)[0]
                    return "Good morning, Jay." if "> Good morning." in new else ""
                return ""

        backend = GreetingBackend()
        loop, _ = self.make_loop(backend)
        loop.hear("Jay", "Good morning.")
        loop.cognitive_cycle("idle")
        replies = [text for _, kind, text in loop.journal.dump(100) if kind == "spoken"]
        self.assertEqual(replies, ["Good morning, Jay."])

    def test_behavior_prompt_contains_no_raw_hidden_numeric_state(self):
        backend = RecordingBackend(initiation=["REST"], speech=[""])
        loop, _ = self.make_loop(backend)
        loop.set_hidden("hunger", 97.321)
        loop.cognitive_cycle("idle")
        speech_prompt = [
            user for system, user, _, _ in backend.calls if "say anything aloud" in system.lower()
        ][0]
        self.assertNotIn("97.321", speech_prompt)
        self.assertIn("I'm starving", speech_prompt)

    def test_temporal_frame_marks_no_new_event_after_behavior_opportunity(self):
        backend = RecordingBackend(initiation=["REST", "REST"], speech=["", ""])
        loop, _ = self.make_loop(backend)
        loop.hear("Jay", "Good morning.")
        loop.cognitive_cycle("idle")
        speech_prompts = [
            user for system, user, _, _ in backend.calls if "say anything aloud" in system.lower()
        ]
        self.assertIn("> Good morning.", speech_prompts[0])
        self.assertIn(
            "NEW FIRST-PERSON EXPERIENCE SINCE THE PREVIOUS BEHAVIOR OPPORTUNITY:\nNone.",
            speech_prompts[1],
        )

    def test_diagnostic_behavior_renderer_receives_runtime_trigger_label(self):
        backend = RecordingBackend(initiation=["REST"], speech=[""])
        loop, _ = self.make_loop(backend)
        loop.cognitive_cycle("developer_only_condition_name")
        speech_prompt = [
            user for system, user, _, _ in backend.calls if "say anything aloud" in system.lower()
        ][0]
        self.assertIn("CURRENT OPPORTUNITY:\ndeveloper_only_condition_name", speech_prompt)

    @unittest.expectedFailure
    def test_behavior_after_multi_thought_episode_can_access_entire_current_thought_chain(self):
        """Earlier thoughts in the current episode disappear from the behavior prompt."""
        backend = TwoThoughtBackend()
        loop, _ = self.make_loop(backend)
        thoughts = loop.cognitive_cycle("conversation")
        self.assertEqual(len(thoughts), 2)
        speech_prompt = [
            user for system, user, _, _ in backend.calls if "say anything aloud" in system.lower()
        ][0]
        self.assertIn("The answer I want to give Jay is violet.", speech_prompt)
        self.assertIn("Yes. That settles what I should say.", speech_prompt)

    @unittest.expectedFailure
    def test_action_decision_can_see_speech_that_just_occurred_in_same_opportunity(self):
        """Speech is recorded before action, but action receives the cached pre-speech prompt."""
        backend = SpeechThenActionBackend()
        loop, _ = self.make_loop(backend, allow_movement=True)
        loop.cognitive_cycle("conversation")
        action_prompt = [
            user for system, user, _, _ in backend.calls if "physical action" in system.lower()
        ][0]
        self.assertIn("I will stay exactly where I am.", action_prompt)

    @unittest.expectedFailure
    def test_pending_new_experience_survives_restart_as_new_for_next_behavior_opportunity(self):
        """The behavior freshness watermark is in-memory and resets to the DB tail on restart."""
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        path = Path(td.name) / "restart.sqlite3"

        first_backend = RecordingBackend()
        first = CharacterLoop(PRETORIUS_IDENTITY, first_backend, path, seed=1)
        first.hear("Jay", "Please answer this after you restart.", think=False)
        first.journal.conn.close()

        second_backend = RecordingBackend(initiation=["REST"], speech=[""])
        second = CharacterLoop(PRETORIUS_IDENTITY, second_backend, path, seed=1)
        self.addCleanup(second.journal.conn.close)
        second.cognitive_cycle("conversation")
        speech_prompt = [
            user for system, user, _, _ in second_backend.calls if "say anything aloud" in system.lower()
        ][0]
        new_section = speech_prompt.split(
            "NEW FIRST-PERSON EXPERIENCE SINCE THE PREVIOUS BEHAVIOR OPPORTUNITY:", 1
        )[-1].split("MOST RECENT PRIVATE THOUGHT FROM THIS CYCLE:", 1)[0]
        self.assertIn("Please answer this after you restart.", new_section)

    @unittest.expectedFailure
    def test_behavior_renderer_is_not_given_developer_runtime_condition_label(self):
        """A stronger experiential-firewall interpretation would exclude scheduler metadata."""
        backend = RecordingBackend(initiation=["REST"], speech=[""])
        loop, _ = self.make_loop(backend)
        loop.cognitive_cycle("developer_only_condition_name")
        speech_prompt = [
            user for system, user, _, _ in backend.calls if "say anything aloud" in system.lower()
        ][0]
        self.assertNotIn("developer_only_condition_name", speech_prompt)


if __name__ == "__main__":
    unittest.main()
