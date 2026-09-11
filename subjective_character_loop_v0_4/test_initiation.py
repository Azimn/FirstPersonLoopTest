from subjective_loop import ScriptedBackend
from test_support import LoopTestCase, RecordingBackend


class InitiationTests(LoopTestCase):
    def test_rest_produces_no_private_thought_but_can_still_speak(self):
        backend = RecordingBackend(
            initiation=["REST"],
            private=["This must never be called."],
            speech=["Good morning."],
        )
        loop, _ = self.make_loop(backend)
        self.assertEqual(loop.cognitive_cycle("conversation"), [])
        kinds = [kind for _, kind, _ in loop.journal.dump()]
        self.assertNotIn("thought", kinds)
        self.assertIn("spoken", kinds)
        called_systems = "\n".join(system for system, _, _, _ in backend.calls)
        self.assertNotIn("private inner life", called_systems.lower())
        self.assertIn("say anything aloud", called_systems.lower())

    def test_rest_can_also_remain_behaviorally_silent(self):
        backend = RecordingBackend(initiation=["REST"], speech=[""])
        loop, _ = self.make_loop(backend)
        self.assertEqual(loop.cognitive_cycle("idle"), [])
        self.assertFalse(any(kind in {"thought", "spoken", "action"} for _, kind, _ in loop.journal.dump()))

    def test_think_starts_private_cognition(self):
        backend = RecordingBackend(initiation=["THINK"], private=["Something about that sound bothers me."], probes=["RELEASE"])
        loop, _ = self.make_loop(backend)
        self.assertEqual(loop.cognitive_cycle("event"), ["Something about that sound bothers me."])

    def test_malformed_initiation_defaults_to_rest(self):
        loop, _ = self.make_loop(RecordingBackend(initiation=["I think I should THINK."]))
        self.assertEqual(loop.cognitive_cycle("idle"), [])
        self.assertIn("initiation_malformed", [kind for _, kind, _ in loop.journal.dump_developer()])

    def test_initiation_decision_never_enters_subjective_journal(self):
        loop, _ = self.make_loop(RecordingBackend(initiation=["REST"]))
        loop.cognitive_cycle("idle")
        text = self.journal_text(loop)
        self.assertNotIn("THINK", text)
        self.assertNotIn("REST", text)
        self.assertIn("initiation_decision", [kind for _, kind, _ in loop.journal.dump_developer()])

    def test_initiation_probe_sees_identity_and_subjective_awareness_but_not_hidden_state(self):
        backend = RecordingBackend(initiation=["REST"])
        loop, _ = self.make_loop(backend)
        loop.set_hidden("hunger", 97.321)
        loop.journal.developer("secret", "developer-only-token-xyz")
        loop.cognitive_cycle("idle")
        prompt = [user for system, user, _, _ in backend.calls if "thought-initiation" in system.lower()][0]
        self.assertIn("Dr. Septimus Pretorius", prompt)
        self.assertIn("I'm starving", prompt)
        self.assertNotIn("97.321", prompt)
        self.assertNotIn("developer-only-token-xyz", prompt)

    def test_forced_manual_cycle_bypasses_initiation_for_diagnostics(self):
        backend = RecordingBackend(initiation=["REST"], private=["I can still be forced to think for a test."], probes=["RELEASE"])
        loop, _ = self.make_loop(backend)
        self.assertEqual(loop.cognitive_cycle("manual", force=True), ["I can still be forced to think for a test."])
        self.assertEqual(backend.init_i, 0)

    def test_scripted_backend_contains_both_rest_and_think_opportunities(self):
        loop, _ = self.make_loop(ScriptedBackend())
        lengths = [len(loop.cognitive_cycle(f"tick{i}")) for i in range(5)]
        self.assertIn(0, lengths)
        self.assertTrue(any(length > 0 for length in lengths))
