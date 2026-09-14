from test_support import LoopTestCase, RecordingBackend


class GPT56AdversarialTests(LoopTestCase):
    def test_unknown_provenance_cannot_gain_subjective_authority(self):
        loop, _ = self.make_loop(RecordingBackend())
        accepted = loop._accept_subjective(
            "thought",
            "Pretorius pauses and studies the problem from outside himself.",
            "banana",
        )
        self.assertFalse(accepted)
        self.assertNotIn("studies the problem from outside", self.journal_text(loop))

    def test_legitimate_first_person_theory_of_mind_is_not_false_positive(self):
        text = "I wonder what she thinks about me after that conversation."
        loop, _ = self.make_loop(RecordingBackend())
        self.assertTrue(loop._accept_subjective("thought", text, "private"))
        self.assertIn(text, self.journal_text(loop))

    def test_long_verbatim_private_clause_cannot_be_padded_into_public_speech(self):
        private = (
            "I hid the brass key beneath the blue vase and I do not intend to tell Jay "
            "where it is because I am not ready to explain myself."
        )
        spoken = (
            "I should probably say this directly. I hid the brass key beneath the blue "
            "vase and I do not intend to tell Jay where it is because I am not ready to "
            "explain myself. Anyway, that is all I want to say right now."
        )
        loop, _ = self.make_loop(RecordingBackend())
        self.assertEqual(
            loop._validate_spoken(spoken, private_thought="", private_candidates=[private]),
            "",
        )

    def test_stative_sentence_is_not_a_physical_action(self):
        loop, _ = self.make_loop(RecordingBackend())
        self.assertIsNotNone(loop._action_reject_reason("I am furious."))
        self.assertIsNotNone(loop._action_reject_reason("I feel exhausted."))
        self.assertIsNotNone(loop._action_reject_reason("I want to leave."))

    def test_first_person_speech_wrapper_is_not_public_utterance_content(self):
        loop, _ = self.make_loop(RecordingBackend())
        self.assertEqual(loop._validate_spoken("I say hello to Jay.", private_thought=""), "")

    def test_private_paraphrase_remains_allowed(self):
        private = (
            "I hid the brass key beneath the blue vase because I do not trust Jay with it yet."
        )
        paraphrase = "There is something I am still not ready to share with you."
        loop, _ = self.make_loop(RecordingBackend())
        self.assertEqual(
            loop._validate_spoken(paraphrase, private_thought="", private_candidates=[private]),
            paraphrase,
        )

    def test_speech_prompt_and_privacy_guard_share_one_background_snapshot(self):
        private = (
            "I buried the copper token beneath the old stone planter and I have not told "
            "Jay because I want to keep that private for now."
        )
        backend = RecordingBackend(initiation=["REST"], speech=[private])
        loop, _ = self.make_loop(backend)
        self.assertTrue(loop._accept_subjective("thought", private, "private"))
        loop._behavior_seen_episode_id = loop.journal.last_episode_id()

        calls = []
        original = loop.journal.recent_background_rows_at_or_before

        def counted(max_id, limit=6):
            calls.append((max_id, limit))
            return original(max_id, limit)

        loop.journal.recent_background_rows_at_or_before = counted
        loop.cognitive_cycle("idle")

        self.assertEqual(len(calls), 1)
        self.assertFalse(
            any(kind == "spoken" and text == private for _, kind, text in loop.journal.dump())
        )
