from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional


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
        "hunger": -1,
        "fatigue": -1,
        "pain": -1,
        "temperature_discomfort": -1,
        "boredom": -1,
        "interest": -1,
    })
    consciously_noticed: dict[str, bool] = field(default_factory=lambda: {
        "hunger": False,
        "fatigue": False,
        "pain": False,
        "temperature_discomfort": False,
        "boredom": False,
        "interest": False,
    })


class ExperienceCompiler:
    """Translate hidden scalar state into first-person subjective language."""

    BANDS = (20, 40, 65, 85)

    def __init__(self, rng: random.Random, memory: Optional[ThresholdMemory] = None) -> None:
        self.rng = rng
        self.memory = memory or ThresholdMemory()

    def _band(self, value: float) -> int:
        return sum(1 for threshold in self.BANDS if value >= threshold)

    def prime(self, state: HiddenState) -> None:
        for channel in self.memory.last_band:
            self.memory.last_band[channel] = self._band(getattr(state, channel))

    def to_json(self) -> dict[str, object]:
        return {
            "last_band": self.memory.last_band,
            "consciously_noticed": self.memory.consciously_noticed,
        }

    @classmethod
    def memory_from_json(cls, data: object) -> Optional[ThresholdMemory]:
        if not isinstance(data, dict):
            return None
        try:
            return ThresholdMemory(
                last_band={k: int(v) for k, v in dict(data["last_band"]).items()},
                consciously_noticed={k: bool(v) for k, v in dict(data["consciously_noticed"]).items()},
            )
        except (KeyError, TypeError, ValueError):
            return None

    def threshold_injections(self, state: HiddenState) -> list[str]:
        output: list[str] = []
        for channel in self.memory.last_band:
            current = self._band(getattr(state, channel))
            previous = self.memory.last_band[channel]
            if current == previous:
                continue
            if current > previous:
                text = self._render_level(channel, current, state)
                if text:
                    output.append(text)
                    self.memory.consciously_noticed[channel] = True
            elif self.memory.consciously_noticed[channel]:
                text = self._render_easing(channel, current)
                if text:
                    output.append(text)
                if current == 0:
                    self.memory.consciously_noticed[channel] = False
            self.memory.last_band[channel] = current
        return output

    def recurrent_injections(self, state: HiddenState) -> list[str]:
        output: list[str] = []
        for channel in ("hunger", "pain", "boredom", "interest", "fatigue", "temperature_discomfort"):
            value = getattr(state, channel)
            if value < 65:
                continue
            probability = min(0.78, 0.12 + ((value - 65.0) / 35.0) * 0.55)
            if self.rng.random() < probability:
                text = self._render_level(channel, self._band(value), state)
                if text:
                    output.append(text)
                    self.memory.consciously_noticed[channel] = True
        return output

    @staticmethod
    def _render_easing(channel: str, current_band: int) -> str:
        if current_band <= 0:
            return {
                "hunger": "I'm not hungry anymore.",
                "fatigue": "I don't feel tired anymore.",
                "pain": "The pain is gone.",
                "temperature_discomfort": "I feel physically comfortable again.",
                "boredom": "I'm not bored anymore.",
                "interest": "That fascination has finally loosened its grip on me.",
            }[channel]
        return {
            "hunger": "My hunger is easing.",
            "fatigue": "I feel a little less tired now.",
            "pain": "The pain is easing.",
            "temperature_discomfort": "I'm starting to feel more physically comfortable.",
            "boredom": "I'm not nearly as bored now.",
            "interest": "My fascination with this is beginning to loosen its grip on my attention.",
        }[channel]

    @staticmethod
    def _render_level(channel: str, band: int, state: HiddenState) -> str:
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
