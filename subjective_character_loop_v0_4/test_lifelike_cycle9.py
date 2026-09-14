import unittest

from lifelike import FirstPersonLife
from test_support import LoopTestCase, RecordingBackend


class StubRng:
    def __init__(self, values):
        self.values = iter(values)

    def random(self):
        return next(self.values)


class LifelikeCycle9Tests(LoopTestCase):
    def test_unresolved_concern_can_return_without_new_external_cue(self):
        life = FirstPersonLife()
        concern = "I still do not know why Henry left without saying goodbye."
        life.observe_thought(concern)
        returned = life.advance(1800.0, StubRng([0.0, 0.0]))
        self.assertEqual(returned, [concern])
        rendered = life.render_private_context()
        self.assertIn("Without my deciding to", rendered)
        self.assertIn(concern, rendered)

    def test_spontaneous_return_has_refractory_gap(self):
        life = FirstPersonLife()
        concern = "I still do not know why Henry left without saying goodbye."
        life.observe_thought(concern)
        life.advance(1800.0, StubRng([0.0, 0.0]))
        self.assertEqual(life.advance(1800.0, StubRng([])), [])
        self.assertNotIn("Without my deciding to", life.render_private_context())

    def test_no_carried_issue_means_nothing_spontaneously_returns(self):
        life = FirstPersonLife()
        self.assertEqual(life.advance(3600.0, StubRng([0.0])), [])
        self.assertNotIn("drifted back", life.render_private_context())

    def test_foreground_context_is_not_a_complete_internal_dashboard(self):
        life = FirstPersonLife()
        concerns = [
            "I still do not know what the red door was hiding.",
            "I still need to understand why the garden gate was unlocked.",
            "I keep coming back to the missing train ticket.",
            "I wonder why Henry never answered the letter.",
            "I am not ready to decide what the broken lamp means.",
            "I still need to ask Morgan about the old photograph.",
        ]
        for concern in concerns:
            life.observe_thought(concern)
        rendered = life.render_private_context(limit=3)
        visible = sum(1 for concern in concerns if concern in rendered)
        self.assertLessEqual(visible, 3)
        self.assertGreater(visible, 0)

    def test_recurrence_state_survives_serialization_in_natural_language(self):
        life = FirstPersonLife()
        concern = "I keep wondering why the attic window was open."
        life.observe_thought(concern)
        life.advance(1800.0, StubRng([0.0, 0.0]))
        restored = FirstPersonLife.from_json(life.to_json())
        rendered = restored.render_private_context().lower()
        self.assertIn("attic window", rendered)
        self.assertIn("without my deciding to", rendered)
        self.assertNotIn("recurrence score", rendered)
        self.assertNotIn("timer", rendered)
        self.assertNotIn("salience", rendered)

    def test_runtime_advance_gives_life_substrate_a_time_opportunity(self):
        loop, _ = self.make_loop(RecordingBackend(), seed=1)
        calls = []

        def record_advance(seconds, rng=None):
            calls.append((seconds, rng))
            return []

        loop.life.advance = record_advance
        loop.advance(17.0, think=False)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], 17.0)
        self.assertIs(calls[0][1], loop.rng)


if __name__ == "__main__":
    unittest.main()
