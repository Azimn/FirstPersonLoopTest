from pathlib import Path

path = Path("loopcore.py")
text = path.read_text(encoding="utf-8")

old_background = '''    def recent_background_at_or_before(self, max_id: int, limit: int = 6) -> list[str]:
        rows = self.conn.execute(
            "SELECT text FROM episodes "
            "WHERE id <= ? AND kind IN ('experience', 'thought', 'memory') "
            "ORDER BY id DESC LIMIT ?",
            (max_id, limit),
        ).fetchall()
        return [row[0] for row in reversed(rows)]
'''
new_background = '''    def recent_background_rows_at_or_before(
        self,
        max_id: int,
        limit: int = 6,
    ) -> list[tuple[str, str]]:
        rows = self.conn.execute(
            "SELECT kind, text FROM episodes "
            "WHERE id <= ? AND kind IN ('experience', 'thought', 'memory') "
            "ORDER BY id DESC LIMIT ?",
            (max_id, limit),
        ).fetchall()
        return [(str(kind), str(text)) for kind, text in reversed(rows)]

    def recent_background_at_or_before(self, max_id: int, limit: int = 6) -> list[str]:
        return [
            text
            for _, text in self.recent_background_rows_at_or_before(max_id, limit)
        ]
'''
if old_background not in text and new_background not in text:
    raise SystemExit("cycle4 journal background anchor not found")
text = text.replace(old_background, new_background, 1)

old_signature = '''    def _behavior_prompt(
        self,
        thought_episode: list[str],
        after_id: Optional[int] = None,
    ) -> str:
'''
new_signature = '''    def _behavior_prompt(
        self,
        thought_episode: list[str],
        after_id: Optional[int] = None,
        background_rows: Optional[list[tuple[str, str]]] = None,
    ) -> str:
'''
if old_signature not in text and new_signature not in text:
    raise SystemExit("cycle4 behavior signature anchor not found")
text = text.replace(old_signature, new_signature, 1)

old_prompt_background = '''        new_experience = self.journal.new_experiential_text_since(watermark)
        background = self.journal.recent_background_at_or_before(watermark, limit=6)
        new_text = "\\n\\n".join(new_experience) if new_experience else "None."
'''
new_prompt_background = '''        new_experience = self.journal.new_experiential_text_since(watermark)
        if background_rows is None:
            background_rows = self.journal.recent_background_rows_at_or_before(
                watermark,
                limit=6,
            )
        background = [text for _, text in background_rows]
        new_text = "\\n\\n".join(new_experience) if new_experience else "None."
'''
if old_prompt_background not in text and new_prompt_background not in text:
    raise SystemExit("cycle4 prompt background anchor not found")
text = text.replace(old_prompt_background, new_prompt_background, 1)

old_behavior = '''    def _consider_outward_behavior(self, thought_episode: list[str]) -> None:
        opportunity_start = self._behavior_seen_episode_id
        speech_prompt = self._behavior_prompt(
            thought_episode,
            after_id=opportunity_start,
        )
'''
new_behavior = '''    def _consider_outward_behavior(self, thought_episode: list[str]) -> None:
        opportunity_start = self._behavior_seen_episode_id
        speech_background_rows = self.journal.recent_background_rows_at_or_before(
            opportunity_start,
            limit=6,
        )
        speech_prompt = self._behavior_prompt(
            thought_episode,
            after_id=opportunity_start,
            background_rows=speech_background_rows,
        )
'''
if old_behavior not in text and new_behavior not in text:
    raise SystemExit("cycle4 behavior snapshot anchor not found")
text = text.replace(old_behavior, new_behavior, 1)

old_sql = '''        # Privacy invariant: every private thought visible to the speech renderer
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
'''
new_sql = '''        # Privacy invariant: the speech renderer and copy guard share the same
        # immutable background snapshot for this behavior opportunity.
        visible_private = [
            thought.strip() for thought in thought_episode if thought.strip()
        ]
        visible_private.extend(
            text for kind, text in speech_background_rows if kind == "thought"
        )
'''
if old_sql not in text and new_sql not in text:
    raise SystemExit("cycle4 privacy SQL anchor not found")
text = text.replace(old_sql, new_sql, 1)

path.write_text(text, encoding="utf-8")
