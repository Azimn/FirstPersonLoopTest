import unittest

from lifelike import FirstPersonLife


class LifelikeCycle7Tests(unittest.TestCase):
    def test_conflicting_stance_survives_as_ambivalence(self):
        life = FirstPersonLife()
        thought = "I want to tell Jay what happened, but part of me still wants to keep it private."
        life.observe_thought(thought)
        self.assertEqual(life.alive_tensions(), [thought])
        rendered = life.render_private_context()
        self.assertIn("tell Jay", rendered)
        self.assertIn("keep it private", rendered)

    def test_ordinary_followup_does_not_magically_resolve_conflict(self):
        life = FirstPersonLife()
        thought = "I trust Jay, but I am still angry with him about what happened."
        life.observe_thought(thought)
        life.observe_thought("I should probably make some tea.")
        self.assertEqual(life.alive_tensions(), [thought])

    def test_explicit_choice_can_resolve_related_ambivalence(self):
        life = FirstPersonLife()
        thought = "I want to tell Jay what happened, but part of me still wants to keep it private."
        life.observe_thought(thought)
        life.observe_thought("I have decided to tell Jay what happened. I am choosing honesty over keeping it private.")
        self.assertEqual(life.alive_tensions(), [])

    def test_rephrased_same_conflict_does_not_multiply(self):
        life = FirstPersonLife()
        life.observe_thought("I trust Jay, but I am still angry with him about what happened.")
        life.observe_thought("Part of me trusts Jay, although I am still angry about what he did.")
        self.assertEqual(len(life.alive_tensions()), 1)

    def test_ambivalence_persists_through_serialization(self):
        life = FirstPersonLife()
        thought = "I want to leave, but I also want to stay long enough to understand this."
        life.observe_thought(thought)
        restored = FirstPersonLife.from_json(life.to_json())
        self.assertEqual(restored.alive_tensions(), [thought])


if __name__ == "__main__":
    unittest.main()
