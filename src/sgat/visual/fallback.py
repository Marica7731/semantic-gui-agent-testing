"""Visual fallback: last-resort localization over OCR text boxes.

The framework never relies on vision for primary localization. When the
semantic matcher fails, an injectable OCR provider gets one chance to find
the target from a screenshot before the action is reported as failed —
errors stay diagnosable, nothing fails silently.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class DetectedText:
    text: str
    bounds: tuple[int, int, int, int]


class OcrProvider(Protocol):
    name: str

    def detect(self, screenshot_png: bytes) -> list[DetectedText]: ...


class NullOcrProvider:
    """Placeholder provider: fails loudly so misconfiguration is noticed."""

    name = "null"

    def detect(self, screenshot_png: bytes) -> list[DetectedText]:
        raise RuntimeError(
            "No OCR provider configured. Construct VisualFallback(provider=...) to enable visual fallback."
        )


class VisualFallback:
    def __init__(self, provider: OcrProvider | None = None) -> None:
        self.provider: OcrProvider = provider or NullOcrProvider()

    @property
    def enabled(self) -> bool:
        return not isinstance(self.provider, NullOcrProvider)

    def resolve(self, screenshot_png: bytes, text: str) -> DetectedText | None:
        """Return the tightest OCR box containing ``text``, or None."""
        best: DetectedText | None = None
        best_score = 0.0
        needle = text.lower()
        if not needle:
            return None
        for detection in self.provider.detect(screenshot_png):
            haystack = detection.text.lower()
            if needle in haystack:
                score = len(needle) / len(haystack)
                if score > best_score:
                    best, best_score = detection, score
        return best
