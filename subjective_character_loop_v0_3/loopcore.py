from __future__ import annotations

import difflib
import json
import random
import sqlite3
import time
from pathlib import Path
from typing import Callable, Optional

from backends import ModelBackend
from experience import ExperienceCompiler, HiddenState

PRIVATE_SYSTEM = """
Continue my private inner life using only the first-person experiences, memories, and
self-description supplied to you. Everything you write is something I privately think.
Write natural first-person English. The thought may be a sentence, a fragment, several
paragraphs, an unanswered question, an internal argument, rehearsal, self-correction,
association, distraction, abandoned reasoning, planning, imagination, or a change of
mind. It does not need to reach a conclusion.

Do not narrate me from outside. Do not write stage directions. Do not speak aloud. Do
not mention prompts, models, databases, variables, scores, continuation controls,
simulation machinery, or hidden implementation. Do not invent facts I could not know
from what is present in my awareness.
""".strip()

CONTINUE_PRIVATE_SYSTEM = """
Let my private thought continue naturally from my current first-person awareness. This
is still inside my own mind. I may stay with the same concern, question it, contradict
myself, drift, remember something already available to me, become distracted, or leave
a thought unfinished. Do not force closure. Do not narrate me from outside and do not
speak aloud. Do not mention runtime controls or implementation.
""".strip()

PROBE_SYSTEM = """
You are making a hidden scheduling judgment using only the subject's recent first-person
awareness and most recent private thought.

Would another immediate private thought naturally follow from this same concern?
Choose CONTINUE only when there is a clear unfinished question, tension, curiosity,
worry, contradiction, plan, possibility, or line of reasoning that would naturally
produce another immediate thought. Otherwise choose RELEASE.

Reply with exactly one word: CONTINUE or RELEASE.
""".strip()

SPEECH_SYSTEM = """
Given my current first-person experience and private thought, decide whether I naturally
say anything aloud now. Silence is valid. If I speak, return only the exact words I say
aloud, with no quotation marks, labels, stage directions, or narration. If I remain
silent, return an empty response. Do not automatically copy private thought into speech.
""".strip()

ACTION_SYSTEM = """
Given my current first-person experience and private thought, decide whether I naturally
perform one simple physical action now. If I act, return one short first-person sentence
such as "I turn toward the window." If I do nothing, return an empty response. Do not
narrate private thought.
""".strip()

INVOLUNTARY_SYSTEM = """
A sudden physical sensation has just entered my awareness. Decide whether I make a very
brief involuntary sound or exclamation before deliberate reflection. Return only the
sound or exact words spoken aloud, or return nothing.
""".strip()


class Journal:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.execute("CREATE TABLE IF NOT EXISTS episodes (id INTEGER PRIMARY KEY AUTOINCREMENT, created REAL NOT NULL, kind TEXT NOT NULL, text TEXT NOT NULL)")
        self.conn.execute("CREATE TABLE IF NOT EXISTS runtime_state (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        self.conn.execute("CREATE TABLE IF NOT EXISTS developer_events (id INTEGER PRIMARY KEY AUTOINCREMENT, created REAL NOT NULL, kind TEXT NOT NULL, detail TEXT NOT NULL)")
        self.conn.commit()

    def add(self, kind: str, text: str) -> None:
        text = text.strip()
        if text:
            self.conn.execute("INSERT INTO episodes(created, kind, text) VALUES (?, ?, ?)", (time.time(), kind, text))
            self.conn.commit()

    def developer(self, kind: str, detail: str) -> None:
        self.conn.execute("INSERT INTO developer_events(created, kind, detail) VALUES (?, ?, ?)", (time.time(), kind, detail))
        self.conn.commit()

    def recent_character_text(self, limit: int = 28) -> list[str]:
        rows = self.conn.execute("SELECT text FROM episodes WHERE kind IN ('experience', 'thought', 'memory') ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [row[0] for row in reversed(rows)]

    def save_json(self, key: str, data: object) -> None:
        self.conn.execute("INSERT INTO runtime_state(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, json.dumps(data)))
        self.conn.commit()

    def load_json(self, key: str) -> Optional[object]:
        row = self.conn.execute("SELECT value FROM runtime_state WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def save_hidden_state(self, state: HiddenState) -> None:
        self.save_json("hidden_state", state.__dict__)

    def load_hidden_state(self) -> Optional[HiddenState]:
        data = self.load_json("hidden_state")
        return HiddenState(**data) if isinstance(data, dict) else None

    def dump(self, limit: int = 50) -> list[tuple[int, str, str]]:
        return self.conn.execute("SELECT id, kind, text FROM episodes ORDER BY id DESC LIMIT ?", (limit,)).fetchall()[::-1]

    def dump_developer(self, limit: int = 50) -> list[tuple[int, str, str]]:
        return self.conn.execute("SELECT id, kind, detail FROM developer_events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()[::-1]


BetweenThoughtsHook = Callable[["CharacterLoop", int], None]


class CharacterLoop:
    def __init__(self, identity: str, backend: ModelBackend, db_path: Path, seed: Optional[int] = None,
                 allow_movement: bool = False, max_continuations: int = 12,
                 thought_tokens: int = 220, speech_tokens: int = 80, probe_tokens: int = 8,
                 debug: bool = False, between_thoughts_hook: Optional[BetweenThoughtsHook] = None) -> None:
        self.identity = identity.strip()
        self.backend = backend
        self.rng = random.Random(seed)
        self.journal = Journal(db_path)
        self.state = self.journal.load_hidden_state() or HiddenState()
        saved_compiler = ExperienceCompiler.memory_from_json(self.journal.load_json("experience_compiler"))
        self.compiler = ExperienceCompiler(self.rng, saved_compiler)
        if saved_compiler is None:
            self.compiler.prime(self.state)
        self.allow_movement = allow_movement
        self.max_continuations = max(0, int(max_continuations))
        self.thought_tokens = max(16, int(thought_tokens))
        self.speech_tokens = max(8, int(speech_tokens))
        self.probe_tokens = max(2, int(probe_tokens))
        self.debug = debug
        self.between_thoughts_hook = between_thoughts_hook

    def _save_runtime(self) -> None:
        self.journal.save_hidden_state(self.state)
        self.journal.save_json("experience_compiler", self.compiler.to_json())

    def _awareness_prompt(self, limit: int = 28) -> str:
        recent = self.journal.recent_character_text(limit=limit)
        awareness = "\n\n".join(recent) if recent else "I am here with my own thoughts."
        return f"This is who I understand myself to be:\n{self.identity}\n\nThis is what is currently available in my awareness:\n{awareness}"

    def _probe_prompt(self, latest_thought: str) -> str:
        recent = self.journal.recent_character_text(limit=8)
        preceding = recent[:-1] if recent and recent[-1] == latest_thought else recent
        context = "\n\n".join(preceding[-7:]) if preceding else "I am here with my own thoughts."
        return f"Recent first-person awareness:\n{context}\n\nMost recent private thought:\n{latest_thought}"

    def _append_experience(self, text: str) -> None:
        text = text.strip()
        if text:
            self.journal.add("experience", text)
            print(f"  experience: {text}")

    def hear(self, speaker: str, words: str, think: bool = True) -> None:
        words = words.strip()
        if not words:
            return
        self.journal.add("heard_speech", f'{speaker} said: "{words}"')
        self._append_experience(f'I hear {speaker} say, "{words}"')
        self.state.boredom = max(0.0, self.state.boredom - 12.0)
        self.state.clamp()
        self._save_runtime()
        if think:
            self.cognitive_cycle(trigger="conversation")

    def remember(self, recollection: str, think: bool = False) -> None:
        recollection = recollection.strip().rstrip(".")
        if not recollection:
            return
        text = f"I remember {recollection}."
        self.journal.add("memory", text)
        print(f"  memory:     {text}")
        if think:
            self.cognitive_cycle(trigger="memory")

    def experience_opaque_action(self, action_phrase: str, think: bool = False) -> None:
        action_phrase = action_phrase.strip().rstrip(".")
        if not action_phrase:
            return
        self._append_experience(f"I find myself {action_phrase}.")
        if think:
            self.cognitive_cycle(trigger="opaque_action")

    def set_interest(self, value: float, subject: str = "") -> None:
        self.state.interest = value
        self.state.interest_subject = subject.strip()
        self.state.boredom = max(0.0, self.state.boredom - max(0.0, value) * 0.25)
        self.state.clamp()
        self._inject_threshold_changes()
        self._save_runtime()

    def set_hidden(self, channel: str, value: float) -> None:
        if not hasattr(self.state, channel) or channel in {"interest_subject", "seconds_elapsed"}:
            raise ValueError(f"Unknown hidden channel: {channel}")
        setattr(self.state, channel, value)
        self.state.clamp()
        self._inject_threshold_changes()
        self._save_runtime()

    def sudden_pain(self, value: float) -> None:
        previous = self.state.pain
        self.state.pain = max(self.state.pain, value)
        self.state.clamp()
        self._inject_threshold_changes()
        delta = self.state.pain - previous
        spill_probability = min(0.85, max(0.0, delta / 100.0 + self.state.pain / 220.0))
        if self.rng.random() < spill_probability:
            spoken = self.backend.complete(INVOLUNTARY_SYSTEM, self._awareness_prompt(limit=8), temperature=0.7, max_tokens=12).strip()
            spoken = self._validate_spoken(spoken, private_thought="", involuntary=True)
            if spoken:
                self._record_spoken(spoken, involuntary=True)
        self._save_runtime()
        self.cognitive_cycle(trigger="pain")

    def _inject_threshold_changes(self) -> None:
        for text in self.compiler.threshold_injections(self.state):
            self._append_experience(text)

    def advance(self, seconds: float, think: bool = True) -> None:
        seconds = max(0.0, float(seconds))
        self.state.seconds_elapsed += seconds
        minutes = seconds / 60.0
        self.state.hunger += minutes * 0.34
        self.state.fatigue += minutes * 0.20
        self.state.boredom += minutes * (0.32 if self.state.interest < 45 else 0.08)
        self.state.interest -= minutes * 0.18
        self.state.pain -= minutes * 0.22
        self.state.temperature_discomfort -= minutes * 0.10
        self.state.clamp()
        self._inject_threshold_changes()
        for text in self.compiler.recurrent_injections(self.state):
            self._append_experience(text)
        self._save_runtime()
        if think:
            self.cognitive_cycle(trigger="time")

    def idle(self, steps: int, seconds_per_step: float = 30.0) -> None:
        for index in range(max(0, int(steps))):
            print(f"\n[idle step {index + 1}/{steps}]")
            self.advance(seconds_per_step, think=True)

    @staticmethod
    def _looks_like_external_narration(text: str) -> bool:
        stripped = text.strip()
        low = stripped.lower()
        if not stripped or low in {"continue", "release"}:
            return True
        forbidden = ("the character", "pretorius thinks", "kiki thinks", "as pretorius", "as kiki", "system prompt", "language model", "simulation state", "hidden variable", "continuation probe")
        if any(term in low for term in forbidden) or stripped.startswith(("[", "(", "*")):
            return True
        return low.startswith(("a moment of ", "pretorius ", "dr. pretorius ", "kiki ", "he thinks ", "she thinks ", "he feels ", "she feels "))

    def _generate_private(self, continuing: bool) -> str:
        system = CONTINUE_PRIVATE_SYSTEM if continuing else PRIVATE_SYSTEM
        for attempt in range(2):
            if self.debug:
                print(f"  private:    [generating attempt {attempt + 1}...]")
            text = self.backend.complete(system, self._awareness_prompt(), temperature=0.92, max_tokens=self.thought_tokens).strip()
            if text and not self._looks_like_external_narration(text):
                self.journal.add("thought", text)
                print(f"  thought:    {text}")
                return text
            self.journal.developer("private_rejected", text or "<empty>")
        return ""

    def _continuation_decision(self, latest_thought: str) -> str:
        raw = self.backend.complete(PROBE_SYSTEM, self._probe_prompt(latest_thought), temperature=0.0, max_tokens=self.probe_tokens).strip().upper()
        if raw not in {"CONTINUE", "RELEASE"}:
            self.journal.developer("probe_malformed", raw or "<empty>")
            decision = "RELEASE"
        else:
            decision = raw
        self.journal.developer("probe_decision", decision)
        if self.debug:
            print(f"  probe:      [{decision.lower()}]")
        return decision

    def cognitive_cycle(self, trigger: str = "time") -> list[str]:
        thoughts: list[str] = []
        thought = self._generate_private(continuing=False)
        if not thought:
            return thoughts
        thoughts.append(thought)
        continuations = 0
        while True:
            if continuations >= self.max_continuations:
                self.journal.developer("continuation_cap_reached", f"trigger={trigger}; additional_thoughts={continuations}")
                break
            decision = self._continuation_decision(thought)
            if decision == "RELEASE":
                break
            if self.between_thoughts_hook is not None:
                self.between_thoughts_hook(self, len(thoughts))
            next_thought = self._generate_private(continuing=True)
            if not next_thought:
                break
            thought = next_thought
            thoughts.append(thought)
            continuations += 1
        self._consider_outward_behavior(thought)
        self.state.boredom = max(0.0, self.state.boredom - 2.5)
        self.state.clamp()
        self._save_runtime()
        return thoughts

    def _consider_outward_behavior(self, latest_thought: str) -> None:
        if self.debug:
            print("  speech:     [deciding...]")
        spoken = self.backend.complete(SPEECH_SYSTEM, self._awareness_prompt(), temperature=0.72, max_tokens=self.speech_tokens).strip()
        spoken = self._validate_spoken(spoken, latest_thought)
        if spoken:
            self._record_spoken(spoken, involuntary=False)
        else:
            print("  aloud:      [silence]")
        if self.allow_movement:
            action = self.backend.complete(ACTION_SYSTEM, self._awareness_prompt(), temperature=0.7, max_tokens=50).strip()
            if action and not self._looks_like_external_narration(action):
                self.journal.add("action", action)
                print(f"  action:     {action}")
                self._append_experience(self._action_as_experience(action))

    def _validate_spoken(self, spoken: str, private_thought: str, involuntary: bool = False) -> str:
        spoken = spoken.strip()
        if not spoken:
            return ""
        if self._looks_like_external_narration(spoken):
            self.journal.developer("speech_rejected_narration", spoken)
            return ""
        if not involuntary and private_thought and len(private_thought) >= 60:
            ratio = difflib.SequenceMatcher(None, spoken, private_thought).ratio()
            if ratio >= 0.88:
                self.journal.developer("speech_rejected_private_copy", f"ratio={ratio:.3f}")
                return ""
        return spoken

    def _record_spoken(self, spoken: str, involuntary: bool) -> None:
        self.journal.add("spoken", spoken.strip())
        prefix = "I hear myself blurt out" if involuntary else "I hear myself say"
        experience = f'{prefix}, "{spoken.strip()}"'
        print(f"  aloud:      {spoken.strip()}")
        self._append_experience(experience)

    @staticmethod
    def _action_as_experience(action: str) -> str:
        stripped = action.strip()
        return stripped if stripped.lower().startswith("i ") else "I " + stripped[:1].lower() + stripped[1:]

    def show_hidden(self) -> str:
        return json.dumps({
            "hunger": round(self.state.hunger, 1),
            "fatigue": round(self.state.fatigue, 1),
            "pain": round(self.state.pain, 1),
            "temperature_discomfort": round(self.state.temperature_discomfort, 1),
            "boredom": round(self.state.boredom, 1),
            "interest": round(self.state.interest, 1),
            "interest_subject": self.state.interest_subject,
            "seconds_elapsed": round(self.state.seconds_elapsed, 1),
        }, indent=2)
