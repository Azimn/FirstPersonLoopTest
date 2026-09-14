from pathlib import Path

path = Path("loopcore.py")
text = path.read_text(encoding="utf-8")
old = '''        for text in self.compiler.recurrent_injections(self.state):
            self._append_experience(text, provenance="body")
        self._save_runtime()
        if think:
            self.cognitive_cycle(trigger="time")'''
new = '''        for text in self.compiler.recurrent_injections(self.state):
            self._append_experience(text, provenance="body")
        # Time offers the natural-language continuity substrate an opportunity for a
        # carried concern to return on its own. It does not force explicit thought;
        # THINK/REST still belongs to the character-facing cognition loop.
        self.life.advance(seconds, self.rng)
        self._save_runtime()
        if think:
            self.cognitive_cycle(trigger="time")'''
if old not in text:
    if 'self.life.advance(seconds, self.rng)' in text:
        raise SystemExit(0)
    raise RuntimeError("Expected advance block not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
