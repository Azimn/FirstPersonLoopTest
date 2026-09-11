#!/usr/bin/env python3
"""Subjective Character Loop v0.2

Minimal persistent character simulation whose character-facing reality is entirely
first-person natural-language experience. Hidden state remains runtime-only.

v0.2 adds repeated private-thought continuation and autonomous idle stepping while
keeping the character-facing representation narrative and first person.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sqlite3
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

PRIVATE_SYSTEM = """
Continue my private inner thought using only the first-person experiences, memories,
and self-description supplied to you. Everything you write is something I privately
think. Write natural first-person English. I may think briefly or at length, argue with
myself, reconsider something, rehearse possibilities, ruminate, plan, imagine, notice a
conflict, become distracted, or return to an unfinished idea. Do not narrate me from the
outside. Do not write stage directions. Do not speak aloud. Do not mention prompts,
models, databases, variables, scores, simulation machinery, or hidden implementation.
Do not invent facts I could not know from what is present in my awareness.
""".strip()

CONTINUE_SYSTEM = """
Continue my private thought from where it naturally leads. Everything you write is still
inside my own mind. Keep it in first-person natural English. I may continue the same line
of thought, contradict myself, drift, remember something already available to me, or
notice another concern. Do not narrate me from outside and do not speak aloud.
""".strip()

SPEECH_SYSTEM = """
Given my current first-person experience and private thought, decide whether I naturally
say anything aloud now. Silence is allowed. If I speak, return only the exact words I
say aloud, with no quotation marks, labels, stage directions, or narration. If I remain
silent, return an empty response. Do not copy private narration into speech merely
because it is present.
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
sound or words spoken aloud, or return nothing.
""".strip()


class ModelBackend(Protocol):
    def complete(self, system: str, user: str, temperature: float = 0.8, max_tokens: int = 160) -> str: ...


class OllamaBackend:
    def __init__(self, model: str, host: str = "http://127.0.0.1:11434", timeout: int = 180) -> None:
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = timeout

    def complete(self, system: str, user: str, temperature: float = 0.8, max_tokens: int = 160) -> str:
        payload = {
            "model": self.model,
            "stream": True,
            "keep_alive": "10m",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        req = urllib.request.Request(
            f"{self.host}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        chunks: list[str] = []
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                for raw in resp:
                    if not raw.strip():
                        continue
                    packet = json.loads(raw.decode("utf-8"))
                    if packet.get("error"):
                        raise RuntimeError(packet["error"])
                    content = (packet.get("message") or {}).get("content", "")
                    if content:
                        chunks.append(content)
                    if packet.get("done"):
                        break
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ollama HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Could not reach Ollama at {self.host}: {exc}") from exc
        return "".join(chunks).strip()


class ScriptedBackend:
    """Deterministic architectural backend that exercises thought, speech, and silence."""
    def __init__(self) -> None:
        self.private_count = 0
        self.speech_count = 0

    def complete(self, system: str, user: str, temperature: float = 0.8, max_tokens: int = 160) -> str:
        low = system.lower()
        if "private inner thought" in low:
            self.private_count += 1
            if self.private_count == 1:
                return "I keep returning to the unfinished problem. There is something in it I have not understood yet."
            return "Perhaps I have been asking the wrong question. I want to stay with the idea a little longer."
        if "continue my private thought" in low:
            self.private_count += 1
            return "If I turn the assumption around, the problem becomes more interesting rather than less. I should follow that."
        if "say anything aloud" in low:
            self.speech_count += 1
            return "I am considering a problem that has become considerably more interesting." if self.speech_count % 2 else ""
        if "physical action" in low:
            return ""
        if "involuntary" in low:
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
            setattr(self, name, max(0.0, min(100.0, float(getattr(self, name)))))


@dataclass
class ThresholdMemory:
    last_band: dict[str, int] = field(default_factory=lambda: {
        "hunger": -1, "fatigue": -1, "pain": -1,
        "temperature_discomfort": -1, "boredom": -1, "interest": -1,
    })


class Journal:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.execute("CREATE TABLE IF NOT EXISTS episodes (id INTEGER PRIMARY KEY AUTOINCREMENT, created REAL NOT NULL, kind TEXT NOT NULL, text TEXT NOT NULL)")
        self.conn.execute("CREATE TABLE IF NOT EXISTS runtime_state (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        self.conn.commit()

    def add(self, kind: str, text: str) -> None:
        text = text.strip()
        if text:
            self.conn.execute("INSERT INTO episodes(created,kind,text) VALUES (?,?,?)", (time.time(), kind, text))
            self.conn.commit()

    def recent_character_text(self, limit: int = 28) -> list[str]:
        rows = self.conn.execute("SELECT text FROM episodes WHERE kind IN ('experience','thought','memory') ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [r[0] for r in reversed(rows)]

    def save_hidden_state(self, state: HiddenState) -> None:
        self.conn.execute("INSERT INTO runtime_state(key,value) VALUES('hidden_state',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (json.dumps(state.__dict__),))
        self.conn.commit()

    def load_hidden_state(self) -> Optional[HiddenState]:
        row = self.conn.execute("SELECT value FROM runtime_state WHERE key='hidden_state'").fetchone()
        return HiddenState(**json.loads(row[0])) if row else None

    def dump(self, limit: int = 50):
        return self.conn.execute("SELECT id,kind,text FROM episodes ORDER BY id DESC LIMIT ?", (limit,)).fetchall()[::-1]


class ExperienceCompiler:
    BANDS = (20, 40, 65, 85)

    def __init__(self, rng: random.Random) -> None:
        self.rng = rng
        self.memory = ThresholdMemory()

    def _band(self, value: float) -> int:
        return sum(1 for threshold in self.BANDS if value >= threshold)

    def prime(self, state: HiddenState) -> None:
        for channel in self.memory.last_band:
            self.memory.last_band[channel] = self._band(getattr(state, channel))

    def threshold_injections(self, state: HiddenState) -> list[str]:
        out: list[str] = []
        for channel in self.memory.last_band:
            current = self._band(getattr(state, channel))
            previous = self.memory.last_band[channel]
            if current != previous:
                text = self._render_transition(channel, previous, current, state)
                if text:
                    out.append(text)
                self.memory.last_band[channel] = current
        return out

    def recurrent_injections(self, state: HiddenState) -> list[str]:
        out: list[str] = []
        for channel in ("hunger", "pain", "boredom", "interest", "fatigue", "temperature_discomfort"):
            value = getattr(state, channel)
            if value < 65:
                continue
            probability = min(0.78, 0.12 + ((value - 65.0) / 35.0) * 0.55)
            if self.rng.random() < probability:
                text = self._render_level(channel, self._band(value), state)
                if text:
                    out.append(text)
        return out

    def _render_transition(self, channel: str, previous: int, current: int, state: HiddenState) -> str:
        if current > previous:
            return self._render_level(channel, current, state)
        easing = {
            "hunger": "My hunger is easing.",
            "fatigue": "I feel a little less tired now.",
            "pain": "The pain is easing.",
            "temperature_discomfort": "I'm starting to feel more physically comfortable.",
            "boredom": "I'm not nearly as bored now.",
            "interest": "My fascination with this is beginning to loosen its grip on my attention.",
        }
        return easing[channel]

    def _render_level(self, channel: str, band: int, state: HiddenState) -> str:
        if band <= 0:
            return ""
        levels = {
            "hunger": ["", "I'm starting to feel hungry.", "I'm definitely hungry now.", "I'm really hungry. It's becoming difficult to ignore.", "I'm starving. I need to eat, and the thought keeps pushing everything else aside."],
            "fatigue": ["", "I'm starting to feel tired.", "I'm tired enough that concentrating takes more effort.", "I'm exhausted. My thoughts feel heavier than I want them to.", "I'm so tired that staying focused is becoming a struggle."],
            "pain": ["", "Something hurts a little.", "That pain is difficult to ignore.", "I'm in real pain now. It keeps dragging my attention back to it.", "God, that hurts. It's almost impossible to think around it."],
            "temperature_discomfort": ["", "I'm starting to feel uncomfortable from the temperature.", "I'm uncomfortably hot or cold now, and I keep noticing it.", "The temperature is miserable. I want somewhere more comfortable.", "I can barely ignore how physically uncomfortable this feels."],
            "boredom": ["", "I'm beginning to feel bored.", "I'm bored enough that my attention keeps wandering.", "I'm so bored that I'm looking for almost anything else to think about.", "I'm unbearably bored. I want something actually worth my attention."],
            "interest": ["", "Something about this has caught my attention.", "I'm genuinely interested in this now.", "This is fascinating. I keep wanting to return to it and understand more.", "I can't stop thinking about this. I want to follow it as far as it goes."],
        }
        if channel == "interest" and state.interest_subject:
            subject = state.interest_subject.strip().rstrip(".")
            return ["", f"Something about {subject} has caught my attention.", f"I'm genuinely interested in {subject} now.", f"I keep coming back to {subject}. It's fascinating, and I want to understand it better.", f"I can't stop thinking about {subject}. I want to follow the idea as far as it goes."][band]
        return levels[channel][band]


class CharacterLoop:
    def __init__(self, identity: str, backend: ModelBackend, db_path: Path, seed: Optional[int] = None,
                 allow_movement: bool = False, min_thoughts: int = 2, max_thoughts: int = 4,
                 thought_tokens: int = 180, speech_tokens: int = 80) -> None:
        self.identity = identity.strip()
        self.backend = backend
        self.rng = random.Random(seed)
        self.journal = Journal(db_path)
        self.state = self.journal.load_hidden_state() or HiddenState()
        self.compiler = ExperienceCompiler(self.rng)
        self.compiler.prime(self.state)
        self.allow_movement = allow_movement
        self.min_thoughts = max(1, min_thoughts)
        self.max_thoughts = max(self.min_thoughts, max_thoughts)
        self.thought_tokens = thought_tokens
        self.speech_tokens = speech_tokens

    def _awareness_prompt(self) -> str:
        recent = self.journal.recent_character_text()
        awareness = "\n\n".join(recent[-28:]) if recent else "I am here with my own thoughts."
        return f"This is who I understand myself to be:\n{self.identity}\n\nThis is what is currently available in my awareness:\n{awareness}"

    def _append_experience(self, text: str) -> None:
        text = text.strip()
        if text:
            self.journal.add("experience", text)
            print(f"  experience: {text}")

    def hear(self, speaker: str, words: str) -> None:
        words = words.strip()
        if not words:
            return
        self.journal.add("heard_speech", f'{speaker} said: "{words}"')
        self._append_experience(f'I hear {speaker} say, "{words}"')
        self.state.boredom = max(0.0, self.state.boredom - 12.0)
        self.state.clamp(); self.journal.save_hidden_state(self.state)
        self.cycle("conversation")

    def _valid_private(self, text: str) -> bool:
        if not text.strip():
            return False
        bad = ("the character", "pretorius thinks", "stage direction", "as pretorius", "system prompt", "language model", "database", "variable =")
        low = text.lower()
        if any(x in low for x in bad):
            return False
        if re.match(r"^(a moment|pretorius|the doctor|he |she )", text.strip(), re.I):
            return False
        first_person = re.search(r"\b(i|i'm|i've|i'll|me|my|mine)\b", low)
        return bool(first_person)

    def _valid_spoken(self, text: str, private_chain: str) -> bool:
        t = text.strip()
        if not t:
            return True
        if re.match(r"^(a moment|pretorius|the doctor|he |she |i think:|thought:|action:)", t, re.I):
            return False
        if "\n" in t and len(t.splitlines()) > 3:
            return False
        norm_t = re.sub(r"\s+", " ", t.lower())
        norm_p = re.sub(r"\s+", " ", private_chain.lower())
        if len(norm_t) > 40 and norm_t in norm_p:
            return False
        return True

    def think_chain(self, count: Optional[int] = None) -> list[str]:
        count = count or self.rng.randint(self.min_thoughts, self.max_thoughts)
        thoughts: list[str] = []
        for index in range(count):
            system = PRIVATE_SYSTEM if index == 0 else CONTINUE_SYSTEM
            print(f"  private {index+1}/{count}: [generating...]")
            candidate = self.backend.complete(system, self._awareness_prompt(), 0.9, self.thought_tokens).strip()
            if not self._valid_private(candidate):
                print("  private:    [discarded malformed thought]")
                break
            self.journal.add("thought", candidate)
            thoughts.append(candidate)
            print(f"  thought:    {candidate}")
        return thoughts

    def cycle(self, trigger: str = "time") -> list[str]:
        thoughts = self.think_chain()
        private_chain = "\n\n".join(thoughts)
        speech_prompt = self._awareness_prompt()
        print("  speech:     [deciding...]")
        spoken = self.backend.complete(SPEECH_SYSTEM, speech_prompt, 0.72, self.speech_tokens).strip()
        if spoken and self._valid_spoken(spoken, private_chain):
            self._record_spoken(spoken, False)
        elif spoken:
            print("  aloud:      [discarded malformed speech]")
        else:
            print("  aloud:      [silence]")
        if self.allow_movement:
            action = self.backend.complete(ACTION_SYSTEM, speech_prompt, 0.7, 64).strip()
            if action:
                self.journal.add("action", action)
                print(f"  action:     {action}")
                self._append_experience(action if action.lower().startswith("i ") else "I " + action[:1].lower() + action[1:])
        if thoughts:
            self.state.boredom = max(0.0, self.state.boredom - 2.5)
        self.state.clamp(); self.journal.save_hidden_state(self.state)
        return thoughts

    def step(self, seconds: float = 30.0, think: bool = True) -> None:
        seconds = max(0.0, seconds)
        self.state.seconds_elapsed += seconds
        minutes = seconds / 60.0
        self.state.hunger += minutes * 0.34
        self.state.fatigue += minutes * 0.20
        self.state.boredom += minutes * (0.32 if self.state.interest < 45 else 0.08)
        self.state.interest -= minutes * 0.18
        self.state.pain -= minutes * 0.22
        self.state.temperature_discomfort -= minutes * 0.10
        self.state.clamp()
        for text in self.compiler.threshold_injections(self.state) + self.compiler.recurrent_injections(self.state):
            self._append_experience(text)
        self.journal.save_hidden_state(self.state)
        if think:
            self.cycle("idle")

    def run_steps(self, steps: int, seconds_per_step: float = 30.0) -> None:
        for n in range(max(0, steps)):
            print(f"\n[idle step {n+1}/{steps}]")
            self.step(seconds_per_step, think=True)

    def set_hidden(self, channel: str, value: float) -> None:
        if channel not in {"hunger", "fatigue", "pain", "temperature_discomfort", "boredom", "interest"}:
            raise ValueError(f"Unknown hidden channel: {channel}")
        setattr(self.state, channel, value)
        self.state.clamp()
        for text in self.compiler.threshold_injections(self.state):
            self._append_experience(text)
        self.journal.save_hidden_state(self.state)

    def set_interest(self, value: float, subject: str = "") -> None:
        self.state.interest = value
        self.state.interest_subject = subject.strip()
        self.state.boredom = max(0.0, self.state.boredom - value * 0.25)
        self.state.clamp()
        for text in self.compiler.threshold_injections(self.state):
            self._append_experience(text)
        self.journal.save_hidden_state(self.state)

    def sudden_pain(self, value: float) -> None:
        previous = self.state.pain
        self.state.pain = max(self.state.pain, value); self.state.clamp()
        for text in self.compiler.threshold_injections(self.state):
            self._append_experience(text)
        delta = self.state.pain - previous
        p = min(0.85, max(0.0, delta / 100.0 + self.state.pain / 220.0))
        if self.rng.random() < p:
            spoken = self.backend.complete(INVOLUNTARY_SYSTEM, self._awareness_prompt(), 0.7, 24).strip()
            if spoken:
                self._record_spoken(spoken, True)
        self.journal.save_hidden_state(self.state)
        self.cycle("pain")

    def _record_spoken(self, spoken: str, involuntary: bool) -> None:
        self.journal.add("spoken", spoken.strip())
        prefix = "I hear myself blurt out" if involuntary else "I hear myself say"
        print(f"  aloud:      {spoken.strip()}")
        self._append_experience(f'{prefix}, "{spoken.strip()}"')

    def show_hidden(self) -> str:
        return json.dumps(self.state.__dict__, indent=2)


def select_identity(name: str) -> str:
    return PRETORIUS_IDENTITY if name == "pretorius" else KIKI_IDENTITY


def print_help() -> None:
    print("""Developer console commands:
  /step [SECONDS]             advance one idle step and think
  /idle STEPS [SECONDS]       run several autonomous idle steps
  /thought [COUNT]            continue private thought for COUNT generations
  /interest LEVEL SUBJECT     set hidden interest and subject
  /body CHANNEL LEVEL         set a hidden body channel
  /pain LEVEL                 sudden pain, possible involuntary speech
  /state                      inspect hidden developer state
  /journal                    inspect persisted events
  /quit                       exit

Any other text is speech the character hears.""")


def interactive(loop: CharacterLoop, interlocutor: str) -> None:
    print("Subjective Character Loop v0.2")
    print("Character-accessible state is first-person natural language only.")
    print_help(); print()
    while True:
        try:
            raw = input(f"{interlocutor}> ").strip()
        except (EOFError, KeyboardInterrupt):
            print(); break
        if not raw: continue
        if not raw.startswith("/"):
            loop.hear(interlocutor, raw); continue
        parts = raw.split(maxsplit=2); cmd = parts[0].lower()
        try:
            if cmd == "/quit": break
            if cmd == "/step": loop.step(float(parts[1]) if len(parts) > 1 else 30.0)
            elif cmd == "/idle": loop.run_steps(int(parts[1]), float(parts[2]) if len(parts) > 2 else 30.0)
            elif cmd == "/thought": loop.think_chain(int(parts[1]) if len(parts) > 1 else None)
            elif cmd == "/interest": loop.set_interest(float(parts[1]), parts[2] if len(parts) > 2 else "")
            elif cmd == "/body":
                pieces = raw.split(maxsplit=2); loop.set_hidden(pieces[1], float(pieces[2]))
            elif cmd == "/pain": loop.sudden_pain(float(parts[1]))
            elif cmd == "/state": print(loop.show_hidden())
            elif cmd == "/journal":
                for rid, kind, text in loop.journal.dump(): print(f"{rid:04d} {kind:12s} {text}")
            else: print_help()
        except (IndexError, ValueError) as exc:
            print(f"command error: {exc}")


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--character", choices=["pretorius", "kiki"], default="pretorius")
    p.add_argument("--provider", choices=["ollama", "scripted"], default="ollama")
    p.add_argument("--model", default="qwen3:8b")
    p.add_argument("--host", default="http://127.0.0.1:11434")
    p.add_argument("--db", default=None)
    p.add_argument("--interlocutor", default="Jay")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--movement", action="store_true")
    p.add_argument("--min-thoughts", type=int, default=2)
    p.add_argument("--max-thoughts", type=int, default=4)
    p.add_argument("--thought-tokens", type=int, default=180)
    p.add_argument("--speech-tokens", type=int, default=80)
    args = p.parse_args(argv)
    backend: ModelBackend = ScriptedBackend() if args.provider == "scripted" else OllamaBackend(args.model, args.host)
    db = Path(args.db or f"{args.character}_subjective_loop_v02.sqlite3")
    loop = CharacterLoop(select_identity(args.character), backend, db, args.seed, args.movement,
                         args.min_thoughts, args.max_thoughts, args.thought_tokens, args.speech_tokens)
    interactive(loop, args.interlocutor)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
