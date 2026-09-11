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

    def test_external_attributed_speech_may_quote_implementation_like_words(self):
        loop, _ = self.make_loop(RecordingBackend())
        loop.hear("Jay", "Your hunger = 87.321 according to my screen.", think=False)
        self.assertIn("hunger = 87.321", self.journal_text(loop))
        self.assertFalse(any(kind == "ingress_rejected" for _, kind, _ in loop.journal.dump_developer()))

    def test_private_privileged_telemetry_is_rejected_and_retried(self):
        backend = RecordingBackend(
            private=["I can see that hunger = 87.321.", "I'm hungry enough that it is distracting me."],
            probes=["RELEASE"],
        )
        loop, _ = self.make_loop(backend)
        thoughts = loop.cognitive_cycle("test", force=True)
        self.assertEqual(thoughts, ["I'm hungry enough that it is distracting me."])
        self.assertNotIn("87.321", self.journal_text(loop))

    def test_generated_speech_with_telemetry_is_rejected(self):
        backend = RecordingBackend(private=["I should answer."], probes=["RELEASE"], speech=["hunger = 87.321"])
        loop, _ = self.make_loop(backend)
        loop.cognitive_cycle("test", force=True)
        self.assertFalse(any(kind == "spoken" for _, kind, _ in loop.journal.dump()))
        self.assertNotIn("87.321", self.journal_text(loop))

    def test_generated_action_with_implementation_leak_is_rejected(self):
        backend = RecordingBackend(private=["I should move."], probes=["RELEASE"], actions=["I inspect database variable = 0.7"])
        loop, _ = self.make_loop(backend, allow_movement=True)
        loop.cognitive_cycle("test", force=True)
        self.assertFalse(any(kind == "action" for _, kind, _ in loop.journal.dump()))
        self.assertNotIn("database variable", self.journal_text(loop).lower())

    def test_involuntary_speech_with_implementation_leak_is_rejected(self):
        backend = RecordingBackend(involuntary=["SYSTEM: database variable = 0.9"], initiation=["REST"])
        loop, _ = self.make_loop(backend, seed=2)
        self.assertEqual(loop._validate_spoken("SYSTEM: database variable = 0.9", "", involuntary=True), "")
        self.assertIn("speech_rejected_ingress", [kind for _, kind, _ in loop.journal.dump_developer()])

    def test_memory_ingress_rejects_raw_implementation_state(self):
        loop, _ = self.make_loop(RecordingBackend())
        loop.remember("hunger = 87.321", think=False)
        self.assertNotIn("87.321", self.journal_text(loop))
        self.assertIn("ingress_rejected", [kind for _, kind, _ in loop.journal.dump_developer()])

    def test_opaque_action_ingress_rejects_implementation_state(self):
        loop, _ = self.make_loop(RecordingBackend())
        loop.experience_opaque_action("inspecting database variable = 0.7", think=False)
        self.assertNotIn("database variable", self.journal_text(loop).lower())

    def test_probe_sees_only_character_accessible_text(self):
        backend = RecordingBackend(private=["Why does this still bother me?"], probes=["RELEASE"])
        loop, _ = self.make_loop(backend)
        loop.set_hidden("hunger", 97.321)
        loop.cognitive_cycle("test", force=True)
        probe_user = [user for system, user, _, _ in backend.calls if "hidden continuation judgment" in system.lower()][0]
        self.assertNotIn("97.321", probe_user)
        self.assertNotIn("hunger =", probe_user)
        self.assertIn("I'm starving", probe_user)

    def test_malformed_third_person_private_narration_is_retried(self):
        backend = RecordingBackend(private=["A moment of confusion as Pretorius considers the problem.", "I dislike that I still cannot explain this cleanly."], probes=["RELEASE"])
        loop, _ = self.make_loop(backend)
        thoughts = loop.cognitive_cycle("test", force=True)
        self.assertEqual(thoughts, ["I dislike that I still cannot explain this cleanly."])
        self.assertNotIn("A moment of confusion", self.journal_text(loop))

    def test_private_copy_is_rejected_as_speech(self):
        private = "I keep turning this elaborate problem over because the contradiction has not gone away, and I want to know exactly which assumption is responsible for it."
        loop, _ = self.make_loop(RecordingBackend(private=[private], probes=["RELEASE"], speech=[private]))
        loop.cognitive_cycle("test", force=True)
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
                packets = [{"message": {"content": "I keep "}, "done": False}, {"message": {"content": "thinking."}, "done": True}]
                data = "".join(json.dumps(packet) + "\n" for packet in packets).encode("utf-8")
                self.send_response(200); self.send_header("Content-Type", "application/x-ndjson"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
            def log_message(self, format, *args):
                pass
        server = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.shutdown); self.addCleanup(server.server_close)
        backend = OllamaBackend("tiny-test", f"http://127.0.0.1:{server.server_port}", timeout=5)
        self.assertEqual(backend.complete("system", "user", max_tokens=37), "I keep thinking.")
        self.assertTrue(captured["payload"]["stream"])
        self.assertEqual(captured["payload"]["options"]["num_predict"], 37)
