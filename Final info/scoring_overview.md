# Scoring Overview

## Three metrics, one Total

Every response is scored on three metrics by the LLM. They are
combined into a single Total Score. All scores are 0–100.

## TA — Task Achievement

For each item in `task_requirements` AND each item in `task_type_checks`,
the LLM marks PASS or FAIL using a strict two-condition test (see
`prompts/task_achievement.md`).

```
TA = round((passes / total) × 100)         clamp 0-100
```

`total` = number of task_requirements + number of task_type_checks.

## IE — Intelligibility & Effect

The LLM scores 0–100 against a banded scale (see `prompts/intelligibility_effect.md`).
Independent of TA and CQ. Measures *only* clarity and communicative effect —
not whether the student answered the question.

## CQ — Content Quality

For each item in the question's `development_markers` (which includes
the generic 4th "Additional on-topic development" requirement — see
question creation rules), the LLM scores 0–3 against a development ladder.
See `prompts/content_quality.md`.

```
total_score = sum of 0-3 scores across all requirements
max_score   = number_of_requirements × 3
CQ          = round((total_score / max_score) × 100)    clamp 0-100
```

## Total Score

```
Total = (TA × 0.4) + (IE × 0.1) + (CQ × 0.5)
```

Translation:
- TA + IE together = 50% of the Total, weighted 80/20 toward TA.
- CQ = 50% of the Total.

All four scores (TA, IE, CQ, Total) are 0–100. No further adjustments.

## Why these weights

Decided after variance testing on 10 B1 essays. CQ carries half the
weight because it is the metric that most directly answers "did the
student develop their argument?". TA confirms structure; IE confirms
readability. The 0.4 / 0.1 / 0.5 split emerged from comparing AZE
to OpenAI and Claude baselines on the same essays.
