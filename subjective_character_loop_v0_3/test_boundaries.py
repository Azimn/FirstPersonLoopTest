import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from subjective_loop import CharacterLoop, OllamaBackend, PRETORIUS_IDENTITY
from test_support import LoopTestCase, RecordingBackend


class BoundaryTests(LoopTestCase):
    def test_heard_speech_becomes_first_person_experience(self):
        backend = RecordingBackend()
        loop, _ = self.make_loop(backend)
        loop.hear("Jay", "Good morning.", think=False)
        self.assertIn('I hear Jay say, "Good morning."', self.journal_text(loop))
        self.assertNotIn("Jay said:", "\n".join(user for _, user, _, _ in backend.calls))

    def test_probe_sees_only_character_accessible_text(self):
        backend = RecordingBackend(private=["Why does this still bother me?"], probes=["RELEASE"])
        loop, _ = self.make_loop(backend)
        loop.set_hidden("hunger", 97.321)
        loop.cognitive_cycle("test")
        probe_user = [user for system, user, _, _ in backend.calls if "hidden scheduling judgment" in system.lower()][0]
        self.assertNotIn("97.321", probe_user)
        self.assertNotIn("hunger =", probe_user)
        self.assertIn("I'm starving", probe_user)

    def test_malformed_third_person_private_narration_is_retried(self):
        backend = RecordingBackend(private=["A moment of confusion as Pretorius considers the problem.", "I dislike that I still cannot explain this cleanly."], probes=["RELEASE"])
        loop, _ = self.make_loop(backend)
        thoughts = loop.cognitive_cycle("test")
        self.assertEqual(thoughts, ["I dislike that I still cannot explain this cleanly."])
        self.assertNotIn("A moment of confusion", self.journal_text(loop))

    def test_private_copy_is_rejected_as_speech(self):
        private = "I keep turning this elaborate problem over because the contradiction has not gone away, and I want to know exactly which assumption is responsible for it."
        loop, _ = self.make_loop(RecordingBackend(private=[private], probes=["RELEASE"], speech=[private]))
        loop.cognitive_cycle("test")
        self.assertFalse(any(kind == "spoken" for _, kind, _ in loop.journal.dump(limit=50)))
        self.assertIn("speech_rejected_private_copy", [kind for _, kind, _ in loop.journal.dump_developer(limit=50)])

    def test_relief_requires_prior_subjective_awareness(self):
        loop, _ = self.make_loop(RecordingBackend())
        loop.set_interest(19, "")
        self.assertNotIn("fascination", self.journal_text(loop).lower())
        loop.set_interest(70, "synthetic life")
        self.assertIn("synthetic life", self.journal_text(loop))
        loop.set_interest(30, "synthetic life")
        self.assertIn("loosen", self.journal_text(loop))

    def test_compiler_awareness_persists_restart(self):
        loop, path = self.make_loop(RecordingBackend())
        loop.set_hidden("hunger", 90)
        self.assertIn("starving", self.journal_text(loop).lower())
        loop2 = CharacterLoop(PRETORIUS_IDENTITY, RecordingBackend(), path, seed=1)
        self.addCleanup(loop2.journal.conn.close)
        loop2.set_hidden("hunger", 30)
        self.assertIn("hunger is easing", self.journal_text(loop2).lower())

    def test_opaque_action_exposes_consequence_not_cause(self):
        loop, _ = self.make_loop(RecordingBackend())
        loop.experience_opaque_action("standing beside the table", think=False)
        text = self.journal_text(loop)
        self.assertIn("I find myself standing beside the table.", text)
        self.assertNotIn("because", text.lower())

    def test_ollama_streaming_transport_and_token_cap(self):
        captured = {}
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                captured["payload"] = json.loads(self.rfile.read(length).decode("utf-8"))
                packets = [
                    {"message": {"content": "I keep "}, "done": False},
                    {"message": {"content": "thinking."}, "done": True},
                ]
                data = "".join(json.dumps(packet) + "\n" for packet in packets).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/x-ndjson")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            def log_message(self, format, *args):
                pass
        server = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.shutdown)
        self.addCleanup(server.server_close)
        backend = OllamaBackend("tiny-test", f"http://127.0.0.1:{server.server_port}", timeout=5)
        self.assertEqual(backend.complete("system", "user", max_tokens=37), "I keep thinking.")
        self.assertTrue(captured["payload"]["stream"])
        self.assertEqual(captured["payload"]["options"]["num_predict"], 37)
