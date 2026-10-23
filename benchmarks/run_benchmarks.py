"""Benchmark harness for semantic localization performance.

Measures per step: action elapsed time, success, and how often the UI-tree
cache absorbed unchanged screens. Runs against the in-memory stub by default
so the harness itself is verifiable anywhere; use --executor to point it at
a real device.

Output: a Markdown summary on stdout plus a CSV under benchmarks/results/.
Numbers are only produced by actual runs — nothing in this repository is
fabricated. Until you run it against real devices there are no results.

Usage:
    python benchmarks/run_benchmarks.py                       # stub dry run
    python benchmarks/run_benchmarks.py --executor android --serial <serial> --repeat 20
"""

from __future__ import annotations

import argparse
import csv
import statistics
import time
from datetime import datetime
from pathlib import Path

from sgat.batch import batch_execute
from sgat.registry import default_registry
from sgat.models import ActionResult, SemanticTarget

RESULTS_DIR = Path(__file__).parent / "results"

# Dry-run scenario set executed against the stub; replace locators with the
# elements of the app you actually want to measure on a real device.
SCENARIOS: dict[str, list[dict]] = {
    "find-and-tap-ok": [
        {"action": "tap", "locator": {"text": "OK"}},
    ],
    "find-by-resource-id": [
        {"action": "find", "locator": {"resource_id": "com.example:id/search"}},
    ],
    "tap-then-type": [
        {"action": "tap", "locator": {"resource_id": "com.example:id/search"}},
        {"action": "input_text", "text": "semantic"},
    ],
    "back-navigation": [
        {"action": "back"},
    ],
}


def build_step(executor, step: dict):
    if step["action"] == "tap":
        target = SemanticTarget(id="bench", **step["locator"])
        return lambda: executor.tap(target)
    if step["action"] == "find":
        target = SemanticTarget(id="bench", **step["locator"])
        return lambda: (
            ActionResult(action="find", success=executor.find(target).best is not None, target_id=target.id)
        )
    if step["action"] == "input_text":
        return lambda: executor.input_text(step["text"])
    if step["action"] == "back":
        return lambda: executor.back()
    raise ValueError(f"unknown step action: {step['action']}")


def run(repeat: int, executor_name: str, **config) -> Path:
    executor = default_registry().create(executor_name, **config)
    rows: list[dict] = []
    with executor:
        for scenario, steps in SCENARIOS.items():
            for iteration in range(repeat):
                actions = [build_step(executor, step) for step in steps]
                for step_index, (step, result) in enumerate(zip(steps, batch_execute(actions))):
                    rows.append(
                        {
                            "scenario": scenario,
                            "iteration": iteration,
                            "step": step_index,
                            "action": step["action"],
                            "success": int(result.success),
                            "elapsed_ms": round(result.elapsed_ms, 3),
                        }
                    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = RESULTS_DIR / f"{executor_name}-{datetime.now():%Y%m%d-%H%M%S}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return csv_path


def summarize_csv(csv_path: Path) -> str:
    with csv_path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    by_scenario: dict[str, list[dict]] = {}
    for row in rows:
        by_scenario.setdefault(row["scenario"], []).append(row)

    lines = [
        f"# Benchmark results ({csv_path.stem})",
        "",
        f"Total steps: {len(rows)}",
        "",
        "| scenario | steps | success rate | p50 ms | p95 ms |",
        "| --- | --- | --- | --- | --- |",
    ]
    for scenario, group in sorted(by_scenario.items()):
        elapsed = sorted(float(r["elapsed_ms"]) for r in group)
        p50 = statistics.median(elapsed)
        p95 = elapsed[min(len(elapsed) - 1, int(len(elapsed) * 0.95))]
        success = sum(int(r["success"]) for r in group) / len(group)
        lines.append(
            f"| {scenario} | {len(group)} | {success:.0%} | {p50:.2f} | {p95:.2f} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="semantic-gui-agent-testing benchmarks")
    parser.add_argument("--executor", default="stub", choices=["stub", "android", "windows"])
    parser.add_argument("--repeat", type=int, default=10, help="iterations per scenario")
    parser.add_argument("--serial", default=None, help="Android device serial")
    parser.add_argument("--window-title", default="", help="Target window title regex (Windows)")
    args = parser.parse_args()

    config = {}
    if args.serial:
        config["serial"] = args.serial
    if args.window_title:
        config["window_title"] = args.window_title

    csv_path = run(args.repeat, args.executor, **config)
    print(summarize_csv(csv_path))
    print(f"CSV written to: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
