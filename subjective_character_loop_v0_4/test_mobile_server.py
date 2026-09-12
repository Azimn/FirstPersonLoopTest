import tempfile
import unittest
from pathlib import Path

from backends import ScriptedBackend
from loopcore import CharacterLoop
from mobile_server import MobileController, STATIC_DIR
from personas import PRETORIUS_IDENTITY


class MobileServerTests(unittest.TestCase):
    def make_controller(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        loop = CharacterLoop(
            PRETORIUS_IDENTITY,
            ScriptedBackend(),
            Path(temp.name) / "mobile.sqlite3",
            seed=1,
            max_continuations=6,
        )
        self.addCleanup(loop.journal.conn.close)
        return MobileController(
            loop,
            character="pretorius",
            provider="scripted",
            model="scripted",
            interlocutor="Jay",
        )

    def test_mobile_assets_exist(self):
        self.assertTrue((STATIC_DIR / "index.html").is_file())
        self.assertTrue((STATIC_DIR / "manifest.webmanifest").is_file())

    def test_message_runs_frozen_loop_and_returns_new_events(self):
        controller = self.make_controller()
        result = controller.message("Good morning, Doctor.")
        self.assertTrue(result["ok"])
        self.assertGreater(result["last_id"], 0)
        self.assertTrue(result["events"])
        kinds = {event["kind"] for event in result["events"]}
        self.assertIn("experience", kinds)
        self.assertTrue(kinds.intersection({"thought", "spoken"}))

    def test_idle_and_body_controls_use_normal_loop_paths(self):
        controller = self.make_controller()
        controller.set_body("hunger", 90)
        state = controller.status()["hidden_state"]
        self.assertEqual(state["hunger"], 90.0)
        result = controller.idle(30)
        self.assertTrue(result["ok"])
        self.assertIn("events", result)

    def test_rejects_unknown_body_channel(self):
        controller = self.make_controller()
        with self.assertRaises(ValueError):
            controller.set_body("secret_metric", 50)


if __name__ == "__main__":
    unittest.main()
