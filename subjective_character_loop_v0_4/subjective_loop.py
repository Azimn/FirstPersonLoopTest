#!/usr/bin/env python3
"""Subjective Character Loop v0.4.3 command-line entry point."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from backends import ModelBackend, OllamaBackend, ScriptedBackend
from experience import HiddenState
from loopcore import CharacterLoop, INITIATION_SYSTEM, PROBE_SYSTEM, SubjectiveIngressGate
from personas import KIKI_IDENTITY, PRETORIUS_IDENTITY, select_identity


def print_help() -> None:
    print(
        """
Developer console commands:
  /step [SECONDS]             advance one idle step; initiation may THINK or REST
  /idle STEPS [SECONDS]       run several autonomous cognitive opportunities
  /thought                    force one private-thought cycle (bypasses THINK/REST)
  /interest LEVEL SUBJECT     set hidden interest and subject
  /body CHANNEL LEVEL         set a hidden body channel
  /pain LEVEL                 sudden pain, possible involuntary speech
  /opaque ACTION              experience an action without its hidden cause
  /remember TEXT              add a first-person recollection
  /state                      inspect hidden developer state
  /journal                    inspect subjective/public event journal
  /devlog                     inspect developer-only diagnostics
  /help                       show this text
  /quit                       exit

Any other text is speech the character hears.
""".strip()
    )


def interactive(loop: CharacterLoop, interlocutor: str) -> None:
    print("Subjective Character Loop v0.4.3")
    print("Character-accessible state is first-person natural language only.")
    print("THINK/REST gates explicit private thought only; behavior remains separately available.")
    print("CONTINUE/RELEASE controls the duration of a thought episode once it begins.")
    print("Behavior sees the full current thought episode and temporally framed experience.")
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
            try:
                loop.hear(interlocutor, raw)
            except RuntimeError as exc:
                print(f"runtime error: {exc}")
            continue
        parts = raw.split(maxsplit=2)
        cmd = parts[0].lower()
        try:
            if cmd == "/quit":
                break
            if cmd == "/help":
                print_help()
            elif cmd == "/step":
                loop.advance(float(parts[1]) if len(parts) > 1 else 30.0, think=True)
            elif cmd == "/idle":
                loop.idle(int(parts[1]), float(parts[2]) if len(parts) > 2 else 30.0)
            elif cmd == "/thought":
                loop.cognitive_cycle(trigger="manual", force=True)
            elif cmd == "/interest":
                loop.set_interest(float(parts[1]), parts[2] if len(parts) > 2 else "")
            elif cmd == "/body":
                if len(parts) < 3:
                    print("usage: /body CHANNEL LEVEL")
                    continue
                loop.set_hidden(parts[1], float(parts[2]))
            elif cmd == "/pain":
                loop.sudden_pain(float(parts[1]))
            elif cmd == "/opaque":
                phrase = raw[len("/opaque"):].strip()
                if not phrase:
                    print("usage: /opaque ACTION_PHRASE")
                    continue
                loop.experience_opaque_action(phrase, think=True)
            elif cmd == "/remember":
                loop.remember(raw[len("/remember"):].strip(), think=True)
            elif cmd == "/state":
                print(loop.show_hidden())
            elif cmd == "/journal":
                for row_id, kind, text in loop.journal.dump(limit=40):
                    print(f"{row_id:04d} {kind:14s} {text}")
            elif cmd == "/devlog":
                for row_id, kind, detail in loop.journal.dump_developer(limit=40):
                    print(f"{row_id:04d} {kind:26s} {detail}")
            else:
                print("Unknown command. Use /help.")
        except (IndexError, ValueError, RuntimeError) as exc:
            print(f"command error: {exc}")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Minimal first-person subjective character loop v0.4.3")
    parser.add_argument("--character", choices=["pretorius", "kiki"], default="pretorius")
    parser.add_argument("--provider", choices=["ollama", "scripted"], default="ollama")
    parser.add_argument("--model", default="qwen3:8b", help="Ollama model name")
    parser.add_argument("--host", default="http://127.0.0.1:11434")
    parser.add_argument("--db", default=None, help="SQLite journal path")
    parser.add_argument("--interlocutor", default="Jay")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--movement", action="store_true")
    parser.add_argument("--max-continuations", type=int, default=12)
    parser.add_argument("--thought-tokens", type=int, default=220)
    parser.add_argument("--speech-tokens", type=int, default=80)
    parser.add_argument("--probe-tokens", type=int, default=8)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args(argv)

    db_path = Path(args.db) if args.db else Path(f"{args.character}_subjective_loop_v043.sqlite3")
    backend: ModelBackend = ScriptedBackend() if args.provider == "scripted" else OllamaBackend(args.model, args.host)
    loop = CharacterLoop(
        select_identity(args.character), backend, db_path,
        seed=args.seed, allow_movement=args.movement,
        max_continuations=args.max_continuations,
        thought_tokens=args.thought_tokens, speech_tokens=args.speech_tokens,
        probe_tokens=args.probe_tokens, debug=args.debug,
    )
    interactive(loop, args.interlocutor)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CharacterLoop", "HiddenState", "INITIATION_SYSTEM", "KIKI_IDENTITY", "ModelBackend",
    "OllamaBackend", "PRETORIUS_IDENTITY", "PROBE_SYSTEM", "ScriptedBackend",
    "SubjectiveIngressGate", "select_identity",
]
