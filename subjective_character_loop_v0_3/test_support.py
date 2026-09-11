import tempfile
import unittest
from pathlib import Path

from subjective_loop import CharacterLoop, PRETORIUS_IDENTITY


class RecordingBackend:
    def __init__(self, private=None, probes=None, speech=None):
        self.private = list(private or ["I am thinking about this."])
        self.probes = list(probes or ["RELEASE"])
        self.speech = list(speech or [""])
        self.calls = []
        self.private_i = 0
        self.probe_i = 0
        self.speech_i = 0

    def complete(self, system, user, temperature=0.8, max_tokens=160):
        self.calls.append((system, user, temperature, max_tokens))
        low = system.lower()
        if "hidden scheduling judgment" in low:
            if self.probe_i >= len(self.probes):
                return "RELEASE"
            out = self.probes[self.probe_i]
            self.probe_i += 1
            return out
        if "say anything aloud" in low:
            if self.speech_i >= len(self.speech):
                return ""
            out = self.speech[self.speech_i]
            self.speech_i += 1
            return out
        if "private inner life" in low or "private thought continue" in low:
            if self.private_i >= len(self.private):
                return self.private[-1] if self.private else ""
            out = self.private[self.private_i]
            self.private_i += 1
            return out
        if "physical action" in low or "involuntary" in low:
            return ""
        return ""


class LoopTestCase(unittest.TestCase):
    def make_loop(self, backend=None, **kwargs):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        path = Path(td.name) / "loop.sqlite3"
        loop = CharacterLoop(PRETORIUS_IDENTITY, backend or RecordingBackend(), path, seed=1, **kwargs)
        self.addCleanup(loop.journal.conn.close)
        return loop, path

    @staticmethod
    def journal_text(loop):
        return "\n".join(text for _, _, text in loop.journal.dump(limit=200))
