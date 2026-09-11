from subjective_loop import ScriptedBackend
from test_support import LoopTestCase, RecordingBackend


class ContinuationTests(LoopTestCase):
    def test_one_thought_cycle_releases_immediately(self):
        loop, _ = self.make_loop(RecordingBackend(private=["I have answered enough for the moment."], probes=["RELEASE"]))
        self.assertEqual(len(loop.cognitive_cycle("test", force=True)), 1)

    def test_semantic_probe_can_extend_to_three_thoughts(self):
        backend = RecordingBackend(
            private=["I am not satisfied with that explanation.", "What exactly am I assuming here?", "There. The hidden assumption is the interesting part."],
            probes=["CONTINUE", "CONTINUE", "RELEASE"],
        )
        loop, _ = self.make_loop(backend)
        thoughts = loop.cognitive_cycle("test", force=True)
        self.assertEqual(len(thoughts), 3)
        self.assertIn("hidden assumption", thoughts[-1])

    def test_probe_decisions_never_enter_character_journal(self):
        loop, _ = self.make_loop(RecordingBackend(private=["I still have something to examine.", "I can leave it there."], probes=["CONTINUE", "RELEASE"]))
        loop.cognitive_cycle("test", force=True)
        text = self.journal_text(loop)
        self.assertNotIn("CONTINUE", text)
        self.assertNotIn("RELEASE", text)
        self.assertIn("probe_decision", [kind for _, kind, _ in loop.journal.dump_developer(limit=50)])

    def test_malformed_probe_defaults_to_release(self):
        loop, _ = self.make_loop(RecordingBackend(private=["I could keep going, perhaps."], probes=["I think CONTINUE because this is interesting."]))
        self.assertEqual(len(loop.cognitive_cycle("test", force=True)), 1)
        self.assertIn("probe_malformed", [kind for _, kind, _ in loop.journal.dump_developer(limit=50)])

    def test_hard_cap_is_fault_containment_only(self):
        backend = RecordingBackend(private=["I have one more thought.", "And another.", "Still another.", "This would continue forever."], probes=["CONTINUE"] * 20)
        loop, _ = self.make_loop(backend, max_continuations=2)
        thoughts = loop.cognitive_cycle("test", force=True)
        self.assertEqual(len(thoughts), 3)
        self.assertNotIn("cap", self.journal_text(loop).lower())
        self.assertIn("continuation_cap_reached", [kind for _, kind, _ in loop.journal.dump_developer(limit=50)])

    def test_release_does_not_erase_unfinished_thought(self):
        thought = "I still do not know why Henry reacted that way."
        loop, _ = self.make_loop(RecordingBackend(private=[thought], probes=["RELEASE"]))
        loop.cognitive_cycle("test", force=True)
        self.assertIn(thought, loop.journal.recent_character_text())

    def test_short_horizon_recurrence_uses_recent_journal_context(self):
        class RecurrenceBackend(RecordingBackend):
            def complete(self, system, user, temperature=0.8, max_tokens=160):
                self.calls.append((system, user, temperature, max_tokens))
                low = system.lower()
                if "hidden continuation judgment" in low:
                    return "RELEASE"
                if "say anything aloud" in low:
                    return ""
                if "private inner life" in low or "private thought continue" in low:
                    if "Jay say" in user and "Henry" in user:
                        return "I keep coming back to Henry's reaction. Jay's question has pulled it back into focus."
                    return "I still do not know why Henry reacted that way."
                if "hidden thought-initiation judgment" in low:
                    return "THINK"
                return ""
        backend = RecurrenceBackend()
        loop, _ = self.make_loop(backend)
        self.assertEqual(len(loop.cognitive_cycle("initial", force=True)), 1)
        loop.hear("Jay", "Did Henry ever explain himself?", think=False)
        self.assertIn("pulled it back into focus", loop.cognitive_cycle("cue", force=True)[0])
        hidden = loop.journal.load_json("hidden_state")
        self.assertNotIn("active_topic", hidden)
        self.assertNotIn("unresolved", hidden)

    def test_between_thoughts_hook_can_interrupt(self):
        class InterruptionBackend(RecordingBackend):
            def complete(self, system, user, temperature=0.8, max_tokens=160):
                self.calls.append((system, user, temperature, max_tokens))
                low = system.lower()
                if "hidden continuation judgment" in low:
                    self.probe_i += 1
                    return "CONTINUE" if self.probe_i == 1 else "RELEASE"
                if "say anything aloud" in low:
                    return ""
                if "private inner life" in low:
                    return "I almost have the argument in place."
                if "private thought continue" in low:
                    self.interruption_seen = "I'm suddenly very hungry." in user
                    return "The hunger is distracting, but I can still see where the argument was going."
                return ""
        backend = InterruptionBackend(); backend.interruption_seen = False
        def interrupt(loop, thought_count):
            if thought_count == 1:
                loop._append_experience("I'm suddenly very hungry.", provenance="body")
        loop, _ = self.make_loop(backend, between_thoughts_hook=interrupt)
        self.assertEqual(len(loop.cognitive_cycle("test", force=True)), 2)
        self.assertTrue(backend.interruption_seen)

    def test_continuation_probe_gets_character_accessible_identity_and_no_hidden_state(self):
        backend = RecordingBackend(private=["Why does this still bother me?"], probes=["RELEASE"])
        loop, _ = self.make_loop(backend)
        loop.set_hidden("hunger", 97.321)
        loop.cognitive_cycle("test", force=True)
        prompt = [user for system, user, _, _ in backend.calls if "hidden continuation judgment" in system.lower()][0]
        self.assertIn("Dr. Septimus Pretorius", prompt)
        self.assertIn("I'm starving", prompt)
        self.assertNotIn("97.321", prompt)

    def test_scripted_backend_produces_variable_nonzero_chain_lengths_when_forced(self):
        loop, _ = self.make_loop(ScriptedBackend())
        lengths = [len(loop.cognitive_cycle(f"cycle{i}", force=True)) for i in range(3)]
        self.assertIn(1, lengths)
        self.assertTrue(any(length > 1 for length in lengths))
        self.assertGreater(len(set(lengths)), 1)
