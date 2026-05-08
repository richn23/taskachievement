# AZE Writing Scorer — Locked Specification (v1.0)

This folder contains the locked rules and prompts for the AZE Writing Scorer.
It is the source of truth for the dev team to build the production version.

## Contents

```
Final info/
├── README.md                     this file
├── scoring_overview.md           how the three scores combine
├── question_creation_rules.md    rules for writing new questions
├── prompts/
│   ├── task_achievement.md       TA prompt (sent to LLM)
│   ├── intelligibility_effect.md IE prompt (sent to LLM)
│   └── content_quality.md        CQ prompt (sent to LLM)
├── config/
│   ├── task_type_requirements.json  format checks per task type
│   └── question_markers.example.json sample question metadata (7 B1 essays)
└── examples/
    └── question_template.json    blank question metadata template
```

## Pipeline (high-level)

For each student response the scorer makes three LLM calls:

1. **TA** (Task Achievement) — `prompts/task_achievement.md`
2. **IE** (Intelligibility & Effect) — `prompts/intelligibility_effect.md`
3. **CQ** (Content Quality) — `prompts/content_quality.md`

Each call returns JSON. The scorer combines them into a Total Score:

    Total = (TA × 0.4) + (IE × 0.1) + (CQ × 0.5)

All four scores (TA, IE, CQ, Total) are 0–100. No CEFR ceilings.

See `scoring_overview.md` for full details.

## Variance baseline (v1.0)

Tested on 10 B1 essays × 10 runs each = 100 scorings.
Average within-essay range across runs:

| Metric | Avg range | Max range |
|--------|-----------|-----------|
| TA     | 1.9       | 8         |
| IE     | 2.8       | 12        |
| CQ     | 10.5      | 25        |
| Total  | 5.8       | 12.5      |

## Version history

- v0.1 — paragraph task, 3-requirement rubric, binary bonus (high CQ wobble).
- v0.5 — added evidence-first CQ extraction, no-double-counting rule.
- v0.8 — added 4th generic requirement (Additional on-topic development),
  removed binary TA bonus.
- v1.0 — added explicit-only rule to CQ; 4th CQ requirement now
  lives in `question_markers.json` (was auto-appended). Locked.



## Note: 3-button authoring flow

The Final info folder includes three AI authoring prompts that wire
the question creation UI's three buttons:

1. **Generate Question** — `prompts/generate_question.md`
   Inputs: CEFR level + task type + topic.
   Output: question stem (framing + instruction + 3 bullets) + suggested word count range.

2. **Generate Task Requirements** — `prompts/generate_task_requirements.md`
   Input: the question stem from step 1 (or pasted manually).
   Output: 3 task requirements (the bullets, lightly normalised).

3. **Generate Quality Markers** — `prompts/generate_quality_markers.md`
   Input: the 3 task requirements from step 2.
   Output: full `development_markers` array (3 specific + 1 verbatim generic).

Together these encode all the rules from `question_creation_rules.md`
in machine-runnable form. The human reviewer's job becomes verification
(run 5 test essays through the scorer; tighten anything with avg-range > 8)
rather than authoring from scratch.

- v1.1 (this) — dropped the literal word NAMED from rung-3 wording.
  Replaced with "concrete specific" that explicitly accepts personal
  anecdotes, hypothetical scenarios, real-world references, or
  developed-generic concepts. Removes a knowledge-test bias where
  students who lacked cultural / news exposure were unfairly penalised.

- v1.2 (this) — tightened the generic 4th requirement to require
  semantic distinctness from the other three. Added a paraphrase
  guard to the CQ scoring prompt: rephrasing an already-credited
  idea scores 0 on the 4th. Prevents long essays that repeat the
  same three points from inflating CQ via the 4th requirement.

- v1.3 (this) — added Rule 7 to the Generate Quality Markers prompt:
  every rung-2 must include a "scores 2, not 3" boundary example that
  mirrors realistic student writing. Anchors the middle rung and stops
  the AI from jumping straight from 1 to 3. Music topic-family row also
  tightened to flag the "two activities without explaining why music
  fits each" pattern.
