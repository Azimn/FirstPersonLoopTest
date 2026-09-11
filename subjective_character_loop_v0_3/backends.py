from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Protocol


class ModelBackend(Protocol):
    def complete(self, system: str, user: str, temperature: float = 0.8, max_tokens: int = 160) -> str:
        ...


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
                        raise RuntimeError(str(packet["error"]))
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
    """Deterministic shell test backend with variable thought-chain lengths."""

    def __init__(self) -> None:
        self.private_count = 0
        self.probe_count = 0
        self.speech_count = 0
        self._probe_script = [
            "CONTINUE", "RELEASE",
            "RELEASE",
            "CONTINUE", "CONTINUE", "RELEASE",
        ]

    def complete(self, system: str, user: str, temperature: float = 0.8, max_tokens: int = 160) -> str:
        low = system.lower()
        if "hidden scheduling judgment" in low:
            value = self._probe_script[self.probe_count % len(self._probe_script)]
            self.probe_count += 1
            return value
        if "private inner life" in low or "private thought continue" in low:
            self.private_count += 1
            examples = [
                "I keep returning to the unfinished problem. Something about my assumption still bothers me.",
                "If I reverse the assumption, the difficulty changes shape rather than disappearing. Why?",
                "No. I am skipping a step. I need to look at what I am taking for granted.",
                "That may be enough for now. I can feel the idea settling without being finished.",
            ]
            return examples[(self.private_count - 1) % len(examples)]
        if "say anything aloud" in low:
            self.speech_count += 1
            return (
                "I am considering a problem that has become considerably more interesting."
                if self.speech_count % 2 else ""
            )
        if "physical action" in low:
            return ""
        if "involuntary" in low:
            return "Ow!"
        return ""
