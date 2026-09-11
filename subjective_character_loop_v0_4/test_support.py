import tempfile
import unittest
from pathlib import Path

from subjective_loop import CharacterLoop, PRETORIUS_IDENTITY


class RecordingBackend:
    def __init__(self, private=None, initiation=None, probes=None, speech=None, actions=None, involuntary=None):
        self.private = list(private or ["I am thinking about this."])
        self.initiation = list(initiation or ["THINK"])
        self.probes = list(probes or ["RELEASE"])
        self.speech = list(speech or [""])
        self.actions = list(actions or [""])
        self.involuntary = list(involuntary or [""])
        self.calls = []
        self.private_i = self.init_i = self.probe_i = self.speech_i = self.action_i = self.invol_i = 0

    @staticmethod
    def _next(values, index, default=""):
        return values[index] if index < len(values) else default

    def complete(self, system, user, temperature=0.8, max_tokens=160):
        self.calls.append((system, user, temperature, max_tokens))
        low = system.lower()
        if "hidden thought-initiation judgment" in low:
            out = self._next(self.initiation, self.init_i, "REST"); self.init_i += 1; return out
        if "hidden continuation judgment" in low:
            out = self._next(self.probes, self.probe_i, "RELEASE"); self.probe_i += 1; return out
        if "say anything aloud" in low:
            out = self._next(self.speech, self.speech_i, ""); self.speech_i += 1; return out
        if "physical action" in low:
            out = self._next(self.actions, self.action_i, ""); self.action_i += 1; return out
        if "involuntary" in low:
            out = self._next(self.involuntary, self.invol_i, ""); self.invol_i += 1; return out
        if "private inner life" in low or "private thought continue" in low:
            if self.private_i >= len(self.private):
                return self.private[-1] if self.private else ""
            out = self.private[self.private_i]; self.private_i += 1; return out
        return ""


class LoopTestCase(unittest.TestCase):
    def make_loop(self, backend=None, **kwargs):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        path = Path(td.name) / "loop.sqlite3"
        seed = kwargs.pop("seed", 1)
        loop = CharacterLoop(PRETORIUS_IDENTITY, backend or RecordingBackend(), path, seed=seed, **kwargs)
        self.addCleanup(loop.journal.conn.close)
        return loop, path

    @staticmethod
    def journal_text(loop):
        return "\n".join(text for _, _, text in loop.journal.dump(limit=300))
