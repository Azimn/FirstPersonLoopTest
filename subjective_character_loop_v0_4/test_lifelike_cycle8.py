import unittest

from lifelike import FirstPersonLife


class LifelikeCycle8Tests(unittest.TestCase):
    def test_future_intention_can_remain_latent_until_relevant_cue(self):
        life = FirstPersonLife()
        intention = "When Jay comes back, I need to ask him about the key."
        life.observe_thought(intention)
        self.assertEqual(life.pending_intentions(), [intention])
        self.assertNotIn("brings back something I meant to do", life.render_private_context())

        unrelated = "I hear Morgan say:\n> The rain finally stopped."
        self.assertEqual(life.process_experience(unrelated, "external_speech"), [unrelated])
        self.assertNotIn("ask him about the key", life.render_private_context())

    def test_relevant_experience_reactivates_latent_intention_naturally(self):
        life = FirstPersonLife()
        intention = "When Jay comes back, I need to ask him about the key."
        life.observe_thought(intention)
        heard = "I hear Jay say:\n> I'm back."
        self.assertEqual(life.process_experience(heard, "external_speech"), [heard])
        rendered = life.render_private_context()
        self.assertIn("brings back something I meant to do", rendered)
        self.assertIn(intention, rendered)

    def test_one_cue_does_not_duplicate_same_intention(self):
        life = FirstPersonLife()
        intention = "When Jay comes back, I need to ask him about the key."
        life.observe_thought(intention)
        life.observe_thought("When Jay comes back, I need to ask him about the key.")
        self.assertEqual(len(life.pending_intentions()), 1)
        heard = "I hear Jay say:\n> I'm back."
        life.process_experience(heard, "external_speech")
        life.process_experience(heard, "external_speech")
        self.assertEqual(len(life.active_intentions()), 1)

    def test_prospective_intention_survives_serialization_before_cue(self):
        life = FirstPersonLife()
        intention = "Next time Morgan mentions the studio, I should ask about the broken light."
        life.observe_thought(intention)
        restored = FirstPersonLife.from_json(life.to_json())
        self.assertEqual(restored.pending_intentions(), [intention])
        heard = "I hear Morgan say:\n> The studio is open again."
        restored.process_experience(heard, "external_speech")
        self.assertIn("broken light", restored.render_private_context())

    def test_prospective_context_never_looks_like_task_manager_telemetry(self):
        life = FirstPersonLife()
        intention = "If Jay asks about dinner, I need to remember the reservation."
        life.observe_thought(intention)
        life.process_experience("I hear Jay say:\n> What about dinner?", "external_speech")
        rendered = life.render_private_context().lower()
        self.assertIn("reservation", rendered)
        self.assertNotIn("priority", rendered)
        self.assertNotIn("task id", rendered)
        self.assertNotIn("due date", rendered)
        self.assertNotIn("activation", rendered)


if __name__ == "__main__":
    unittest.main()
