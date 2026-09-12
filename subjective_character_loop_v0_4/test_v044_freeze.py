from test_support import LoopTestCase, RecordingBackend


class V044FreezeTests(LoopTestCase):
    def test_first_thought_in_long_visible_episode_cannot_be_spoken_verbatim(self):
        secret = (
            "I must keep the first private conclusion entirely to myself because Jay "
            "is not ready to hear it yet."
        )
        later = [
            "I should examine the second implication before I settle anything.",
            "The third possibility is stranger, but it still follows from the premise.",
            "I can separate the fourth question from the first without resolving it.",
            "The fifth thought changes the shape of the problem without answering it.",
            "That is enough for the sixth step; I can release the line for now.",
        ]
        backend = RecordingBackend(
            initiation=["THINK"],
            private=[secret, *later],
            probes=["CONTINUE"] * 5 + ["RELEASE"],
            speech=[secret],
        )
        loop, _ = self.make_loop(backend)

        thoughts = loop.cognitive_cycle("conversation")

        self.assertEqual(len(thoughts), 6)
        self.assertEqual(thoughts[0], secret)
        self.assertFalse(
            any(
                kind == "spoken" and text == secret
                for _, kind, text in loop.journal.dump(limit=100)
            )
        )
        self.assertIn(
            "speech_rejected_private_copy",
            [kind for _, kind, _ in loop.journal.dump_developer(limit=100)],
        )

    def test_oldest_private_thought_visible_in_background_remains_protected(self):
        oldest = (
            "I hid the brass key beneath the blue vase, and I do not intend to tell "
            "Jay where it is."
        )
        thoughts = [
            oldest,
            "I should leave the second matter alone for now.",
            "The third concern is unrelated to the key.",
            "I can postpone the fourth question without difficulty.",
            "The fifth thought is enough; I can let it rest.",
        ]
        backend = RecordingBackend(
            initiation=["THINK"] * 5 + ["REST"],
            private=thoughts,
            probes=["RELEASE"] * 5,
            speech=[""] * 5 + [oldest],
        )
        loop, _ = self.make_loop(backend)

        for _ in range(5):
            loop.cognitive_cycle("idle")

        # The oldest thought is still inside the six-entry background shown to the
        # speech renderer, but it is outside v0.4.3's old four-thought protection set.
        loop.cognitive_cycle("idle")

        self.assertFalse(
            any(
                kind == "spoken" and text == oldest
                for _, kind, text in loop.journal.dump(limit=100)
            )
        )
        self.assertIn(
            "speech_rejected_private_copy",
            [kind for _, kind, _ in loop.journal.dump_developer(limit=100)],
        )
