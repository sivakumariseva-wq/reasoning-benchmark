"""
reasoning-benchmark
-------------------
A mini benchmark for testing step-by-step reasoning in language models.

It loads word problems, asks a "solver" for an answer, extracts the final
answer from free-form reasoning text, and reports accuracy per category.

Solvers:
  baseline  - a deliberately naive heuristic (adds every number it sees)
  file      - read pre-collected model outputs from a JSON file
  claude    - call a Claude model through the Anthropic SDK
              (pip install anthropic; set ANTHROPIC_API_KEY)

Usage:
    python benchmark.py --solver baseline
    python benchmark.py --solver file --outputs sample_outputs.json
    python benchmark.py --solver claude --model claude-haiku-5-5
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from typing import Callable

NUMBER = r"-?\d[\d,]*(?:\.\d+)?"

PROMPT_TEMPLATE = (
    "Solve the problem step by step. "
    "On the last line write 'Answer: <number>'.\n\nProblem: {question}"
)


def load_problems(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def to_number(text: str) -> float | None:
    try:
        return float(text.replace(",", ""))
    except ValueError:
        return None


def extract_answer(text: str) -> float | None:
    """Pull the final numeric answer out of a reasoning trace.

    Priority:
      1. an explicit 'Answer: X' line (last one wins)
      2. a LaTeX-style \\boxed{X}
      3. the last number in the text
    """
    explicit = re.findall(rf"answer\s*[:=]?\s*\$?\s*({NUMBER})", text, flags=re.IGNORECASE)
    if explicit:
        return to_number(explicit[-1])
    boxed = re.findall(rf"\\boxed\{{\s*({NUMBER})\s*\}}", text)
    if boxed:
        return to_number(boxed[-1])
    numbers = re.findall(NUMBER, text)
    return to_number(numbers[-1]) if numbers else None


def is_correct(predicted: float | None, expected: float, tol: float = 1e-6) -> bool:
    return predicted is not None and abs(predicted - expected) <= tol


# ---------------------------------------------------------------- solvers --

def baseline_solver(question: str) -> str:
    """Naive heuristic: add every number in the question. Useful as a floor."""
    nums = [to_number(n) for n in re.findall(NUMBER, question)]
    total = sum(n for n in nums if n is not None)
    return f"Adding everything up gives {total:g}.\nAnswer: {total:g}"


def file_solver(path: str) -> Callable[[str], str]:
    with open(path, encoding="utf-8") as fh:
        outputs = json.load(fh)

    def solve(question: str) -> str:
        return outputs.get(question, "")
    return solve


def claude_solver(model: str) -> Callable[[str], str]:
    try:
        import anthropic
    except ImportError:
        raise SystemExit("Install the SDK first: pip install anthropic")
    client = anthropic.Anthropic()

    def solve(question: str) -> str:
        msg = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(question=question)}],
        )
        return "".join(block.text for block in msg.content if block.type == "text")
    return solve


# ------------------------------------------------------------------- run --

def run(problems: list[dict], solve: Callable[[str], str]) -> dict:
    per_category: dict[str, list[bool]] = defaultdict(list)
    failures = []
    for p in problems:
        output = solve(p["question"])
        predicted = extract_answer(output)
        ok = is_correct(predicted, float(p["answer"]))
        per_category[p.get("category", "general")].append(ok)
        if not ok:
            failures.append({"id": p["id"], "expected": p["answer"], "predicted": predicted})

    all_results = [ok for oks in per_category.values() for ok in oks]
    return {
        "accuracy": round(sum(all_results) / len(all_results), 3) if all_results else 0.0,
        "by_category": {c: round(sum(v) / len(v), 3) for c, v in sorted(per_category.items())},
        "failures": failures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--problems", default="problems.json")
    parser.add_argument("--solver", choices=["baseline", "file", "claude"], default="baseline")
    parser.add_argument("--outputs", help="JSON map of question -> model output (for --solver file)")
    parser.add_argument("--model", default="claude-haiku-5-5")
    args = parser.parse_args(argv)

    if args.solver == "baseline":
        solve = baseline_solver
    elif args.solver == "file":
        if not args.outputs:
            parser.error("--outputs is required with --solver file")
        solve = file_solver(args.outputs)
    else:
        solve = claude_solver(args.model)

    report = run(load_problems(args.problems), solve)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
