import unittest

from lifelike import FirstPersonLife


class LifelikeCycle6Tests(unittest.TestCase):
    def test_unchanged_body_sensation_stops_arriving_as_equally_fresh(self):
        life = FirstPersonLife()
        text = "I'm tired enough that my attention keeps slipping."
        self.assertEqual(life.process_experience(text, "body"), [text])
        self.assertEqual(life.process_experience(text, "body"), [text])
        self.assertEqual(life.process_experience(text, "body"), [])
        self.assertEqual(life.process_experience(text, "body"), [])

    def test_changed_body_sensation_breaks_exact_habituation(self):
        life = FirstPersonLife()
        old = "I'm tired enough that my attention keeps slipping."
        changed = "I'm so tired now that keeping my eyes open takes effort."
        life.process_experience(old, "body")
        life.process_experience(old, "body")
        life.process_experience(old, "body")
        self.assertEqual(life.process_experience(changed, "body"), [changed])

    def test_external_speech_never_disappears_as_habituation(self):
        life = FirstPersonLife()
        heard = "I hear Jay say:\n> Are you listening?"
        for _ in range(6):
            self.assertEqual(life.process_experience(heard, "external_speech"), [heard])

    def test_habituation_survives_restart_serialization(self):
        life = FirstPersonLife()
        text = "My shoulder has the same dull ache again."
        life.process_experience(text, "body")
        life.process_experience(text, "body")
        restored = FirstPersonLife.from_json(life.to_json())
        self.assertEqual(restored.process_experience(text, "body"), [])

    def test_familiarity_store_contains_language_not_hidden_body_numbers(self):
        life = FirstPersonLife()
        text = "My shoulder has the same dull ache again."
        life.process_experience(text, "body")
        life.process_experience(text, "body")
        rendered = "\n".join(life.familiar_experiences())
        self.assertIn("dull ache", rendered)
        self.assertNotIn("activation", rendered.lower())
        self.assertNotIn("salience", rendered.lower())
        self.assertNotRegex(rendered, r"\b0\.\d+\b")


if __name__ == "__main__":
    unittest.main()
