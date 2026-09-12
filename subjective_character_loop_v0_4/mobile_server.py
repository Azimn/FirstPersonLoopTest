#!/usr/bin/env python3
"""iPhone/mobile web harness for Subjective Character Loop v0.4.4.

The cognitive architecture and Ollama model remain on the Windows host. Safari on the
phone is only a thin developer interface over the local network.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import socket
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import parse_qs, urlparse

from backends import ModelBackend, OllamaBackend, ScriptedBackend
from loopcore import CharacterLoop
from personas import select_identity

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "mobile"


class MobileController:
    def __init__(
        self,
        loop: CharacterLoop,
        character: str,
        provider: str,
        model: str,
        interlocutor: str,
    ) -> None:
        self.loop = loop
        self.character = character
        self.provider = provider
        self.model = model
        self.interlocutor = interlocutor

    def _last_id(self) -> int:
        return self.loop.journal.last_episode_id()

    def events_since(self, after_id: int) -> list[dict[str, Any]]:
        rows = self.loop.journal.conn.execute(
            "SELECT id, kind, text FROM episodes WHERE id > ? ORDER BY id",
            (int(after_id),),
        ).fetchall()
        visible = {"experience", "thought", "spoken", "action", "memory"}
        return [
            {"id": int(row_id), "kind": kind, "text": text}
            for row_id, kind, text in rows
            if kind in visible
        ]

    def recent_events(self, limit: int = 80) -> list[dict[str, Any]]:
        rows = self.loop.journal.conn.execute(
            "SELECT id, kind, text FROM episodes ORDER BY id DESC LIMIT ?",
            (max(1, min(int(limit), 200)),),
        ).fetchall()[::-1]
        visible = {"experience", "thought", "spoken", "action", "memory"}
        return [
            {"id": int(row_id), "kind": kind, "text": text}
            for row_id, kind, text in rows
            if kind in visible
        ]

    def _run(self, operation: Callable[[], None]) -> dict[str, Any]:
        before = self._last_id()
        operation()
        return {
            "ok": True,
            "events": self.events_since(before),
            "last_id": self._last_id(),
        }

    def message(self, text: str) -> dict[str, Any]:
        value = str(text).strip()
        if not value:
            raise ValueError("Message cannot be empty.")
        return self._run(lambda: self.loop.hear(self.interlocutor, value, think=True))

    def idle(self, seconds: float = 30.0) -> dict[str, Any]:
        seconds = max(0.0, min(float(seconds), 3600.0))
        return self._run(lambda: self.loop.advance(seconds, think=True))

    def force_thought(self) -> dict[str, Any]:
        return self._run(lambda: self.loop.cognitive_cycle(trigger="mobile_manual", force=True))

    def set_body(self, channel: str, value: float) -> dict[str, Any]:
        allowed = {"hunger", "fatigue", "pain", "temperature_discomfort", "boredom"}
        if channel not in allowed:
            raise ValueError(f"Unsupported body channel: {channel}")
        return self._run(lambda: self.loop.set_hidden(channel, float(value)))

    def set_interest(self, value: float, subject: str) -> dict[str, Any]:
        return self._run(lambda: self.loop.set_interest(float(value), str(subject)))

    def remember(self, text: str) -> dict[str, Any]:
        value = str(text).strip()
        if not value:
            raise ValueError("Memory text cannot be empty.")
        return self._run(lambda: self.loop.remember(value, think=True))

    def opaque_action(self, text: str) -> dict[str, Any]:
        value = str(text).strip()
        if not value:
            raise ValueError("Action text cannot be empty.")
        return self._run(lambda: self.loop.experience_opaque_action(value, think=True))

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "version": "0.4.4-mobile-test",
            "character": self.character,
            "provider": self.provider,
            "model": self.model,
            "interlocutor": self.interlocutor,
            "last_id": self._last_id(),
            "events": self.recent_events(),
            "hidden_state": json.loads(self.loop.show_hidden()),
        }


class MobileHTTPServer(HTTPServer):
    controller: MobileController


class Handler(BaseHTTPRequestHandler):
    server_version = "FirstPersonLoopMobile/0.4.4"

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[mobile] {self.address_string()} - {fmt % args}")

    def _send_json(self, data: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 65536:
            raise ValueError("Invalid request size.")
        raw = self.rfile.read(length)
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object.")
        return data

    def _serve_static(self, relative: str, content_type: Optional[str] = None) -> None:
        target = (STATIC_DIR / relative).resolve()
        if STATIC_DIR.resolve() not in target.parents and target != STATIC_DIR.resolve():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = target.read_bytes()
        guessed = content_type or mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", guessed)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            self._serve_static("index.html", "text/html; charset=utf-8")
            return
        if parsed.path == "/manifest.webmanifest":
            self._serve_static("manifest.webmanifest", "application/manifest+json")
            return
        if parsed.path == "/api/status":
            self._send_json(self.server.controller.status())
            return
        if parsed.path == "/api/events":
            query = parse_qs(parsed.query)
            after = int(query.get("after", ["0"])[0])
            self._send_json({
                "ok": True,
                "events": self.server.controller.events_since(after),
                "last_id": self.server.controller._last_id(),
            })
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            data = self._read_json()
            controller = self.server.controller
            if parsed.path == "/api/message":
                result = controller.message(str(data.get("text", "")))
            elif parsed.path == "/api/idle":
                result = controller.idle(float(data.get("seconds", 30)))
            elif parsed.path == "/api/thought":
                result = controller.force_thought()
            elif parsed.path == "/api/body":
                result = controller.set_body(str(data.get("channel", "")), float(data.get("value", 0)))
            elif parsed.path == "/api/interest":
                result = controller.set_interest(float(data.get("value", 0)), str(data.get("subject", "")))
            elif parsed.path == "/api/remember":
                result = controller.remember(str(data.get("text", "")))
            elif parsed.path == "/api/opaque":
                result = controller.opaque_action(str(data.get("text", "")))
            else:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self._send_json(result)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self._send_json({"ok": False, "error": str(exc)}, status=400)
        except RuntimeError as exc:
            self._send_json({"ok": False, "error": str(exc)}, status=502)
        except Exception as exc:
            self._send_json({"ok": False, "error": f"Unexpected server error: {exc}"}, status=500)


def _local_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("10.255.255.255", 1))
        return str(sock.getsockname()[0])
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "127.0.0.1"
    finally:
        sock.close()


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Local iPhone web harness for Subjective Character Loop v0.4.4")
    parser.add_argument("--character", choices=["pretorius", "kiki"], default="pretorius")
    parser.add_argument("--provider", choices=["ollama", "scripted"], default="ollama")
    parser.add_argument("--model", default="qwen3:8b")
    parser.add_argument("--host", default="http://127.0.0.1:11434", help="Ollama host")
    parser.add_argument("--bind", default="0.0.0.0", help="Web server bind address")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--db", default=None)
    parser.add_argument("--interlocutor", default="Jay")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--movement", action="store_true")
    parser.add_argument("--max-continuations", type=int, default=12)
    parser.add_argument("--thought-tokens", type=int, default=220)
    parser.add_argument("--speech-tokens", type=int, default=80)
    parser.add_argument("--probe-tokens", type=int, default=8)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args(argv)

    backend: ModelBackend = (
        ScriptedBackend()
        if args.provider == "scripted"
        else OllamaBackend(args.model, args.host)
    )
    db_path = Path(args.db) if args.db else Path(f"{args.character}_iphone_v044.sqlite3")
    loop = CharacterLoop(
        select_identity(args.character),
        backend,
        db_path,
        seed=args.seed,
        allow_movement=args.movement,
        max_continuations=args.max_continuations,
        thought_tokens=args.thought_tokens,
        speech_tokens=args.speech_tokens,
        probe_tokens=args.probe_tokens,
        debug=args.debug,
    )
    controller = MobileController(loop, args.character, args.provider, args.model, args.interlocutor)
    server = MobileHTTPServer((args.bind, args.port), Handler)
    server.controller = controller

    lan_ip = _local_ip()
    print("Subjective Character Loop v0.4.4 mobile test harness")
    print(f"Character: {args.character} | Provider: {args.provider} | Model: {args.model}")
    print(f"PC browser: http://127.0.0.1:{args.port}")
    print(f"iPhone on same Wi-Fi: http://{lan_ip}:{args.port}")
    print("Keep this PowerShell window open while testing.")
    print("This server has no internet authentication. Do not port-forward or expose it publicly.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping mobile server.")
    finally:
        server.server_close()
        loop.journal.conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
