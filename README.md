# Reasoning Benchmark

A mini benchmark for checking how well language models handle multi-step word problems
(arithmetic, percentages, rates and logic "trick" questions).

It does three things that real LLM evaluation pipelines do:

1. **Prompts** a solver to reason step by step and end with `Answer: <number>`
2. **Extracts** the final answer from free-form reasoning (explicit answer line → `\boxed{}` → last number)
3. **Scores** accuracy overall and per category, and lists every failure for error analysis

## Quick start

```bash
python benchmark.py --solver baseline                               # naive floor
python benchmark.py --solver file --outputs sample_outputs.json     # saved model outputs
python -m unittest                                                  # tests
```

To evaluate a live Claude model:

```bash
pip install anthropic
set ANTHROPIC_API_KEY=your-key        # macOS/Linux: export ANTHROPIC_API_KEY=your-key
python benchmark.py --solver claude --model claude-haiku-5-5
```

## Error analysis on the sample outputs

`sample_outputs.json` contains hand-written example reasoning traces, including two
deliberately common mistakes:

| Problem | Mistake | Type |
|---------|---------|------|
| `rate-2` (two pipes) | Averaged the times instead of adding the rates (1/6 + 1/3 = 1/2 → 2 h) | Wrong method |
| `logic-3` (sheep) | Subtracted 9 from 17; "all but 9" means 9 remain | Misread the question |

These are the kinds of reasoning errors AI trainers look for when reviewing model output:
the arithmetic is fine, but the model set up the problem wrongly.

## Adding problems

Append to `problems.json`:

```json
{"id": "rate-3", "category": "rates", "question": "...", "answer": 42}
```

Requires Python 3.9+.
