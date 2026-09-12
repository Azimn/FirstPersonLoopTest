from pathlib import Path

path = Path("subjective_character_loop_v0_4/loopcore.py")
text = path.read_text(encoding="utf-8")

old = '''        latest_thought = thought_episode[-1] if thought_episode else ""
        spoken = self._validate_spoken(spoken, latest_thought)
'''
new = '''        # Privacy invariant: every private thought visible to the speech renderer
        # must be inside the copy-protection domain. The renderer sees the full
        # current episode plus up to six background awareness entries.
        background_rows = self.journal.conn.execute(
            "SELECT kind, text FROM episodes "
            "WHERE id <= ? AND kind IN ('experience', 'thought', 'memory') "
            "ORDER BY id DESC LIMIT 6",
            (opportunity_start,),
        ).fetchall()
        visible_private = [
            thought.strip() for thought in thought_episode if thought.strip()
        ]
        visible_private.extend(
            text for kind, text in background_rows if kind == "thought"
        )
        spoken = self._validate_spoken(
            spoken,
            private_thought="",
            private_candidates=visible_private,
        )
'''
if old not in text:
    raise SystemExit("speech validation call site not found")
text = text.replace(old, new, 1)

old = '''    def _validate_spoken(
        self,
        spoken: str,
        private_thought: str,
        involuntary: bool = False,
    ) -> str:
'''
new = '''    def _validate_spoken(
        self,
        spoken: str,
        private_thought: str,
        involuntary: bool = False,
        private_candidates: Optional[list[str]] = None,
    ) -> str:
'''
if old not in text:
    raise SystemExit("speech validator signature not found")
text = text.replace(old, new, 1)

old = '''            candidates: list[str] = []
            if private_thought.strip():
                candidates.append(private_thought.strip())
            candidates.extend(self.journal.recent_accessible_thoughts())
'''
new = '''            candidates: list[str] = []
            if private_thought.strip():
                candidates.append(private_thought.strip())
            if private_candidates is None:
                # Compatibility path for direct validator callers. Normal deliberate
                # speech supplies the exact private set visible in its prompt.
                candidates.extend(self.journal.recent_accessible_thoughts())
            else:
                candidates.extend(private_candidates)
'''
if old not in text:
    raise SystemExit("speech candidate block not found")
text = text.replace(old, new, 1)

text = text.replace(
    "Canonical v0.4.3 loop: episodic thought with temporally framed behavior.",
    "Canonical v0.4.4 loop: visible private content and copy protection are aligned.",
    1,
)
text = text.replace(
    "Compatibility helper; v0.4.3 actions must already be first-person.",
    "Compatibility helper; v0.4.4 actions must already be first-person.",
    1,
)

path.write_text(text, encoding="utf-8")
