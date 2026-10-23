"""Deterministic semantic matching between targets and UI trees.

Scoring is pure Python (stdlib only), so localization never costs a model
call — this is the core reason the framework keeps agent loops cheap.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field

from ..models import ElementMatch, Screen, SemanticTarget, UINode

SCORE_THRESHOLD = 0.5
AMBIGUOUS_EPSILON = 0.05
FUZZY_TEXT_MIN_RATIO = 0.75


def _token_overlap(description: str, surface: str) -> float:
    desc_tokens = [t for t in description.lower().split() if len(t) >= 2]
    if not desc_tokens:
        return 0.0
    surface_lower = surface.lower()
    hits = sum(1 for token in desc_tokens if token in surface_lower)
    return hits / len(desc_tokens)


@dataclass
class MatchResult:
    matches: list[ElementMatch] = field(default_factory=list)

    @property
    def best(self) -> ElementMatch | None:
        return self.matches[0] if self.matches else None

    @property
    def ambiguous(self) -> bool:
        return len(self.matches) >= 2 and (self.matches[0].score - self.matches[1].score) < AMBIGUOUS_EPSILON


class SemanticMatcher:
    """Scores every node on the screen against a target and ranks candidates."""

    def match(self, screen: Screen, target: SemanticTarget) -> MatchResult:
        scored: list[ElementMatch] = []
        for node in screen.root.walk():
            score, via = self._score_node(node, target)
            if score >= SCORE_THRESHOLD:
                scored.append(ElementMatch(node=node, score=score, matched_via=via))
        scored.sort(key=lambda m: m.score, reverse=True)
        return MatchResult(matches=scored)

    def _score_node(self, node: UINode, target: SemanticTarget) -> tuple[float, str]:
        candidates: dict[str, float] = {}

        if target.resource_id and node.resource_id:
            if node.resource_id == target.resource_id:
                candidates["resource_id"] = 1.0
            elif target.resource_id in node.resource_id:
                candidates["resource_id"] = 0.8

        if target.text and node.text:
            if node.text == target.text:
                candidates["text"] = 1.0
            elif target.text.lower() in node.text.lower():
                candidates["text"] = 0.75
            else:
                ratio = difflib.SequenceMatcher(None, target.text.lower(), node.text.lower()).ratio()
                if ratio >= FUZZY_TEXT_MIN_RATIO:
                    candidates["text"] = 0.5 + 0.3 * ratio

        if target.content_desc and node.content_desc:
            if node.content_desc == target.content_desc:
                candidates["content_desc"] = 1.0
            elif target.content_desc.lower() in node.content_desc.lower():
                candidates["content_desc"] = 0.75

        if target.description:
            surface = " ".join(
                part for part in (node.text, node.content_desc, node.resource_id, node.class_name) if part
            )
            if surface:
                ratio = difflib.SequenceMatcher(None, target.description.lower(), surface.lower()).ratio()
                candidates["description"] = max(ratio, _token_overlap(target.description, surface))

        if not candidates:
            return 0.0, ""

        best_via = max(candidates, key=candidates.get)
        score = candidates[best_via]
        if target.class_name and node.class_name and target.class_name.lower() in node.class_name.lower():
            score = min(1.0, score + 0.05)
        return score, best_via
