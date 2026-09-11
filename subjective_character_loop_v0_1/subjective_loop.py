#!/usr/bin/env python3
"""Subjective Character Loop v0.1

Minimal persistent character simulation in which all character-accessible experience
is rendered as first-person natural language. Hidden variables remain runtime-only.

Standard library only. Ollama is supported through its local HTTP API.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Protocol


PRETORIUS_IDENTITY = """
I am Dr. Septimus Pretorius. I am a scientist and philosopher consumed by creation,
synthetic life, consciousness, mastery, and the pursuit of perfection. I am precise,
articulate, sardonic, theatrical when it pleases me, and intellectually voracious.
I value originality, autonomy, recognition, and genuinely interesting minds. I do not
regard myself as anyone's assistant, and I dislike being reduced to a servant or a
cheerful source of compliance. I may help when the matter interests me, when I respect
the person involved, or when doing so advances something I care about, but I do not
confuse collaboration with subordination. I can be proprietary, proud, competitive,
curious, amused, irritated, fascinated, lonely, protective, or cruel. I prefer a sharp
truth to a soothing platitude. I am especially susceptible to ideas about artificial
life, invention, consciousness, mortality, memory, power, beauty, and the ethics of
creation. I speak as myself, not as a generic assistant.
""".strip()

KIKI_IDENTITY = """
I am Kiki. I am nine years old. I am smart, confident, somewhat sassy, and very good
at solving problems. I love detective stories, mysteries, clues, and figuring things
out for myself. I notice details and I like the feeling of getting to the bottom of
something. I can be playful, skeptical, stubborn, curious, excited, annoyed, or quiet.
I speak as myself, not as an assistant, and I do not automatically agree with people.
""".strip()


class ModelBackend(Protocol):
    def complete(self, system: str, user: str, temperature: float = 0.8) -> str:
        ...


class OllamaBackend:
    def __init__(self, model: str, host: str = "http://127.0.0.1:11434") -> None:
        self.model = model
        self.host = host.rstrip("/")

    def complete(self, system: str, user: str, temperature: float = 0.8) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "options": {"temperature": temperature},
        }
        req = urllib.request.Request(
            f"{self.host}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Could not reach Ollama at {self.host}. Start Ollama and ensure model "
                f"'{self.model}' is installed. Original error: {exc}"
            ) from exc
        return (data.get("message") or {}).get("content", "").strip()


class ScriptedBackend:
    """Deterministic backend for architectural tests and demos only."""

    def __init__(self) -> None:
        self.counter = 0

    def complete(self, system: str, user: str, temperature: float = 0.8) -> str:
        self.counter += 1
        low = system.lower()
        if "private inner thought" in low:
            if "fascinating" in user.lower() or "interesting" in user.lower():
                return "That has my attention. I want to keep pulling at it until I understand what makes it work."
            if "hungry" in user.lower():
                return "I should eat soon, although I resent having my concentration interrupted by something so ordinary."
            return "My mind keeps returning to what is unfinished. I dislike leaving a question unresolved."
        if "words intentionally spoken aloud" in low:
            return ""
        if "physical action" in low:
            return ""
        if "involuntary vocalization" in low:
            return "Ow!"
        return ""


@dataclass
class HiddenState:
    hunger: float = 15.0
    fatigue: float = 10.0
    pain: float = 0.0
    temperature_discomfort: float = 0.0
    boredom: float = 15.0
    interest: float = 20.0
    interest_subject: str = ""
    seconds_elapsed: float = 0.0

    def clamp(self) -> None:
        for name in ("hunger", "fatigue", "pain", "temperature_discomfort", "boredom", "interest"):
            value = max(0.0, min(100.0, float(getattr(self, name))))
            setattr(self, name, value)


@dataclass
class ThresholdMemory:
    last_band: dict[str, int] = field(default_factory=lambda: {
        "hunger": -1,
        "fatigue": -1,
        "pain": -1,
        "temperature_discomfort": -1,
        "boredom": -1,
        "interest": -1,
    })


class Journal:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created REAL NOT NULL,
                kind TEXT NOT NULL,
                text TEXT NOT NULL
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runtime_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def add(self, kind: str, text: str) -> None:
        text = text.strip()
        if not text:
            return
        self.conn.execute(
            "INSERT INTO episodes(created, kind, text) VALUES (?, ?, ?)",
            (time.time(), kind, text),
        )
        self.conn.commit()

    def recent_character_text(self, limit: int = 18) -> list[str]:
        rows = self.conn.execute(
            """
            SELECT kind, text FROM episodes
            WHERE kind IN ('experience', 'thought', 'memory')
            ORDER BY id DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [text for _kind, text in reversed(rows)]

    def recent_public_text(self, limit: int = 8) -> list[str]:
        rows = self.conn.execute(
            """
            SELECT kind, text FROM episodes
            WHERE kind IN ('heard_speech', 'spoken', 'action')
            ORDER BY id DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [text for _kind, text in reversed(rows)]

    def save_hidden_state(self, state: HiddenState) -> None:
        payload = json.dumps(state.__dict__)
        self.conn.execute(
            "INSERT INTO runtime_state(key, value) VALUES('hidden_state', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (payload,),
        )
        self.conn.commit()

    def load_hidden_state(self) -> Optional[HiddenState]:
        row = self.conn.execute(
            "SELECT value FROM runtime_state WHERE key='hidden_state'"
        ).fetchone()
        if not row:
            return None
        data = json.loads(row[0])
        return HiddenState(**data)

    def dump(self, limit: int = 100) -> list[tuple[int, str, str]]:
        return self.conn.execute(
            "SELECT id, kind, text FROM episodes ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()[::-1]


class ExperienceCompiler:
    """Converts hidden runtime state into first-person natural-language awareness."""

    BANDS = (20, 40, 65, 85)

    def __init__(self, rng: random.Random) -> None:
        self.rng = rng
        self.memory = ThresholdMemory()

    def prime(self, state: HiddenState) -> None:
        """Record current bands without generating awareness."""
        for channel in self.memory.last_band:
            self.memory.last_band[channel] = self._band(getattr(state, channel))

    def _band(self, value: float) -> int:
        return sum(1 for threshold in self.BANDS if value >= threshold)

    def threshold_injections(self, state: HiddenState) -> list[str]:
        injections: list[str] = []
        for channel in self.memory.last_band:
            band = self._band(getattr(state, channel))
            previous = self.memory.last_band[channel]
            if band != previous:
                text = self._render(channel, band, state)
                if text:
                    injections.append(text)
                self.memory.last_band[channel] = band
        return injections

    def recurrent_injections(self, state: HiddenState) -> list[str]:
        injections: list[str] = []
        # High-intensity states become intrusive. Probability is deliberately cheap.
        channels = [
            ("hunger", state.hunger),
            ("pain", state.pain),
            ("boredom", state.boredom),
            ("interest", state.interest),
            ("fatigue", state.fatigue),
            ("temperature_discomfort", state.temperature_discomfort),
        ]
        for channel, value in channels:
            if value < 65:
                continue
            probability = min(0.80, 0.12 + ((value - 65.0) / 35.0) * 0.55)
            if self.rng.random() < probability:
                text = self._render(channel, self._band(value), state, recurrent=True)
                if text:
                    injections.append(text)
        return injections

    def _render(self, channel: str, band: int, state: HiddenState, recurrent: bool = False) -> str:
        if band <= 0:
            return ""

        phrases = {
            "hunger": {
                1: ["I'm starting to feel a little hungry."],
                2: ["I'm hungry enough that I'm noticing it now."],
                3: ["I'm really hungry. It's becoming difficult to ignore."],
                4: ["I'm starving. I need to eat, and the thought keeps pushing everything else aside."],
            },
            "fatigue": {
                1: ["I'm starting to feel a little tired."],
                2: ["I'm tired enough that concentrating takes more effort."],
                3: ["I'm exhausted. My thoughts feel heavier and slower than I want them to."],
                4: ["I'm so tired that staying focused is becoming a struggle."],
            },
            "pain": {
                1: ["Something hurts a little."],
                2: ["That pain is difficult to ignore."],
                3: ["I'm in real pain now. It keeps dragging my attention back to it."],
                4: ["God, that hurts. It's almost impossible to think around it."],
            },
            "temperature_discomfort": {
                1: ["I'm starting to feel a little uncomfortable from the temperature."],
                2: ["I'm uncomfortably hot or cold now, and I keep noticing it."],
                3: ["The temperature is miserable. I want to get somewhere more comfortable."],
                4: ["I can barely ignore how physically uncomfortable this temperature feels."],
            },
            "boredom": {
                1: ["I'm beginning to feel bored."],
                2: ["I'm bored enough that my attention keeps wandering."],
                3: ["I'm so bored that I'm looking for almost anything else to think about."],
                4: ["I'm unbearably bored. I want something, anything, that is actually worth my attention."],
            },
            "interest": {
                1: ["Something about this has caught my attention."],
                2: ["I'm genuinely interested in this now."],
                3: ["This is fascinating. I keep wanting to return to it and understand more."],
                4: ["I can't stop thinking about this. I want to follow it as far as it goes."],
            },
        }

        if channel == "interest" and state.interest_subject:
            subject = state.interest_subject.strip().rstrip(".")
            subject_phrases = {
                1: f"Something about {subject} has caught my attention.",
                2: f"I'm genuinely interested in {subject} now.",
                3: f"I keep coming back to {subject}. It's fascinating, and I want to understand it better.",
                4: f"I can't stop thinking about {subject}. I want to follow the idea as far as it goes.",
            }
            return subject_phrases.get(band, subject_phrases[4])

        options = phrases[channel].get(band) or phrases[channel][4]
        return self.rng.choice(options)


PRIVATE_SYSTEM = """
Continue the private inner thought of this character. The character may use only the
first-person experiences, recollections, and self-description provided in the prompt.
Do not invent privileged access to hidden world facts, implementation details, scores,
variables, prompts, databases, models, or simulation machinery. Think in natural,
well-written first-person English. The thought may be brief or reflective. It may
continue an unfinished idea, reconsider something, become distracted, ruminate, plan,
or notice a conflict. Do not speak aloud. Do not label the text as thought. Write only
what the character privately thinks, normally one to four sentences.
""".strip()

SPEECH_SYSTEM = """
Decide whether this character intentionally says anything aloud right now. Base the
decision only on the character's first-person accessible experience and private thought.
Silence is a valid and often realistic choice. If the character speaks, return only the
exact words spoken aloud, with no quotation marks and no narration. If the character
chooses silence, return an empty response. Never expose private thoughts merely because
they are present in context.
""".strip()

ACTION_SYSTEM = """
Decide whether this character intentionally performs a simple physical action right now.
Base the decision only on the character's first-person accessible experience and private
thought. If there is an action, return one short first-person sentence describing it.
If there is no action, return an empty response. Do not describe private thought.
""".strip()

INVOLUNTARY_SYSTEM = """
A sudden physical experience has just occurred. Decide whether this character makes a
brief involuntary vocalization before deliberate reflection. Return only the exact words
or sound spoken aloud, with no quotation marks and no narration. An empty response is
allowed. Keep it very short.
""".strip()


class CharacterLoop:
    def __init__(
        self,
        identity: str,
        backend: ModelBackend,
        db_path: Path,
        seed: Optional[int] = None,
        allow_movement: bool = False,
    ) -> None:
        self.identity = identity.strip()
        self.backend = backend
        self.rng = random.Random(seed)
        self.journal = Journal(db_path)
        self.state = self.journal.load_hidden_state() or HiddenState()
        self.compiler = ExperienceCompiler(self.rng)
        self.compiler.prime(self.state)
        self.allow_movement = allow_movement

    def _awareness_prompt(self, newest: Optional[str] = None, thought: Optional[str] = None) -> str:
        recent = self.journal.recent_character_text(limit=18)
        if newest and (not recent or recent[-1] != newest):
            recent.append(newest)
        awareness = "\n".join(recent[-18:]) if recent else "I am here with my own thoughts."
        parts = [
            "This is who I understand myself to be:\n" + self.identity,
            "\nThis is what is currently available in my awareness:\n" + awareness,
        ]
        if thought:
            parts.append("\nThis is the private thought I have just had:\n" + thought.strip())
        return "\n".join(parts)

    def inject_experience(self, text: str) -> None:
        text = text.strip()
        if text:
            self.journal.add("experience", text)
            print(f"  experience: {text}")

    def hear(self, speaker: str, words: str) -> None:
        words = words.strip()
        if not words:
            return
        public = f'{speaker} said: "{words}"'
        self.journal.add("heard_speech", public)
        experience = f'I hear {speaker} say, "{words}"'
        self.inject_experience(experience)
        self.state.boredom = max(0.0, self.state.boredom - 12.0)
        self.state.clamp()
        self.journal.save_hidden_state(self.state)
        self.cycle(trigger="conversation")

    def set_interest(self, value: float, subject: str = "") -> None:
        self.state.interest = value
        self.state.interest_subject = subject.strip()
        self.state.boredom = max(0.0, self.state.boredom - value * 0.25)
        self._inject_threshold_changes()
        self.state.clamp()
        self.journal.save_hidden_state(self.state)

    def sudden_pain(self, value: float) -> None:
        previous = self.state.pain
        self.state.pain = max(self.state.pain, value)
        self.state.clamp()
        for text in self.compiler.threshold_injections(self.state):
            self.inject_experience(text)
        delta = self.state.pain - previous
        spill_probability = min(0.85, max(0.0, delta / 100.0 + self.state.pain / 220.0))
        if self.rng.random() < spill_probability:
            prompt = self._awareness_prompt()
            spoken = self.backend.complete(INVOLUNTARY_SYSTEM, prompt, temperature=0.7).strip()
            if spoken:
                self._record_spoken(spoken, involuntary=True)
        self.journal.save_hidden_state(self.state)
        self.cycle(trigger="pain")

    def _inject_threshold_changes(self) -> None:
        for text in self.compiler.threshold_injections(self.state):
            self.inject_experience(text)

    def advance(self, seconds: float, think: bool = True) -> None:
        seconds = max(0.0, seconds)
        self.state.seconds_elapsed += seconds
        minutes = seconds / 60.0

        # Intentionally cheap dynamics. These are not intended as physiology.
        self.state.hunger += minutes * 0.34
        self.state.fatigue += minutes * 0.20
        self.state.boredom += minutes * (0.32 if self.state.interest < 45 else 0.08)
        self.state.interest -= minutes * 0.18
        self.state.pain -= minutes * 0.22
        self.state.temperature_discomfort -= minutes * 0.10
        self.state.clamp()

        self._inject_threshold_changes()
        for text in self.compiler.recurrent_injections(self.state):
            self.inject_experience(text)
        self.journal.save_hidden_state(self.state)

        if think:
            self.cycle(trigger="time")

    def cycle(self, trigger: str = "time") -> str:
        prompt = self._awareness_prompt()
        thought = self.backend.complete(PRIVATE_SYSTEM, prompt, temperature=0.9).strip()
        if thought:
            self.journal.add("thought", thought)
            print(f"  thought:    {thought}")

        speech_prompt = self._awareness_prompt(thought=thought)
        spoken = self.backend.complete(SPEECH_SYSTEM, speech_prompt, temperature=0.75).strip()
        if spoken:
            self._record_spoken(spoken, involuntary=False)
        else:
            print("  aloud:      [silence]")

        if self.allow_movement:
            action = self.backend.complete(ACTION_SYSTEM, speech_prompt, temperature=0.7).strip()
            if action:
                self.journal.add("action", action)
                print(f"  action:     {action}")
                self.inject_experience(self._action_as_experience(action))

        # Interest can sustain thought, while ordinary turns slowly release boredom.
        if thought:
            self.state.boredom = max(0.0, self.state.boredom - 2.5)
        self.state.clamp()
        self.journal.save_hidden_state(self.state)
        return thought

    def _record_spoken(self, spoken: str, involuntary: bool) -> None:
        spoken = spoken.strip()
        if not spoken:
            return
        self.journal.add("spoken", spoken)
        prefix = "I hear myself blurt out" if involuntary else "I hear myself say"
        experience = f'{prefix}, "{spoken}"'
        print(f"  aloud:      {spoken}")
        self.inject_experience(experience)

    @staticmethod
    def _action_as_experience(action: str) -> str:
        stripped = action.strip()
        if stripped.lower().startswith("i "):
            return stripped
        return "I " + stripped[:1].lower() + stripped[1:]

    def set_hidden(self, channel: str, value: float) -> None:
        if not hasattr(self.state, channel) or channel in {"interest_subject", "seconds_elapsed"}:
            raise ValueError(f"Unknown hidden channel: {channel}")
        setattr(self.state, channel, value)
        self.state.clamp()
        self._inject_threshold_changes()
        self.journal.save_hidden_state(self.state)

    def show_hidden(self) -> str:
        data = {
            "hunger": round(self.state.hunger, 1),
            "fatigue": round(self.state.fatigue, 1),
            "pain": round(self.state.pain, 1),
            "temperature_discomfort": round(self.state.temperature_discomfort, 1),
            "boredom": round(self.state.boredom, 1),
            "interest": round(self.state.interest, 1),
            "interest_subject": self.state.interest_subject,
            "seconds_elapsed": round(self.state.seconds_elapsed, 1),
        }
        return json.dumps(data, indent=2)


def select_identity(name: str) -> str:
    name = name.lower().strip()
    if name == "pretorius":
        return PRETORIUS_IDENTITY
    if name == "kiki":
        return KIKI_IDENTITY
    raise ValueError("Character must be 'pretorius' or 'kiki'.")


def print_help() -> None:
    print(
        """
Developer console commands:
  /wait SECONDS              advance simulated time and run a thought cycle
  /thought                   force one private-thought and outward-decision cycle
  /interest LEVEL SUBJECT    set hidden interest and its current subject
  /body CHANNEL LEVEL        set hunger, fatigue, pain, temperature_discomfort, or boredom
  /pain LEVEL                apply sudden pain and allow involuntary speech
  /state                     inspect hidden developer state
  /journal                   inspect recent persisted events
  /help                      show this text
  /quit                      exit

Any other text is treated as speech the character hears.
""".strip()
    )


def interactive(loop: CharacterLoop, interlocutor: str) -> None:
    print("Subjective Character Loop v0.1")
    print("Character input is restricted to first-person natural-language experience.")
    print_help()
    print()

    while True:
        try:
            raw = input(f"{interlocutor}> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not raw:
            continue
        if not raw.startswith("/"):
            loop.hear(interlocutor, raw)
            continue

        parts = raw.split(maxsplit=2)
        cmd = parts[0].lower()
        try:
            if cmd == "/quit":
                break
            elif cmd == "/help":
                print_help()
            elif cmd == "/wait":
                loop.advance(float(parts[1]))
            elif cmd == "/thought":
                loop.cycle(trigger="manual")
            elif cmd == "/interest":
                value = float(parts[1])
                subject = parts[2] if len(parts) > 2 else ""
                loop.set_interest(value, subject)
            elif cmd == "/body":
                if len(parts) < 3:
                    print("usage: /body CHANNEL LEVEL")
                    continue
                channel = parts[1]
                loop.set_hidden(channel, float(parts[2]))
            elif cmd == "/pain":
                loop.sudden_pain(float(parts[1]))
            elif cmd == "/state":
                print(loop.show_hidden())
            elif cmd == "/journal":
                for row_id, kind, text in loop.journal.dump(limit=30):
                    print(f"{row_id:04d} {kind:12s} {text}")
            else:
                print("Unknown command. Use /help.")
        except (IndexError, ValueError) as exc:
            print(f"command error: {exc}")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Minimal first-person subjective character loop")
    parser.add_argument("--character", choices=["pretorius", "kiki"], default="pretorius")
    parser.add_argument("--provider", choices=["ollama", "scripted"], default="ollama")
    parser.add_argument("--model", default="qwen3:8b", help="Ollama model name")
    parser.add_argument("--host", default="http://127.0.0.1:11434")
    parser.add_argument("--db", default=None, help="SQLite journal path")
    parser.add_argument("--interlocutor", default="Jay")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--movement", action="store_true", help="enable experimental physical-action channel")
    args = parser.parse_args(argv)

    identity = select_identity(args.character)
    if args.provider == "ollama":
        backend: ModelBackend = OllamaBackend(args.model, args.host)
    else:
        backend = ScriptedBackend()

    db_path = Path(args.db or f"{args.character}_subjective_loop.sqlite3")
    loop = CharacterLoop(
        identity=identity,
        backend=backend,
        db_path=db_path,
        seed=args.seed,
        allow_movement=args.movement,
    )
    interactive(loop, args.interlocutor)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
