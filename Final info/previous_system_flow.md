# Previous System — End-to-end flow (for dev team)

How writing was scored before the AZE Writing Scorer rebuild.

## Step 1 — Question created (loosely defined)

A question stem is written. There are no explicit task requirements and no explicit Content Quality measures. The question simply describes what the candidate should write about. Anything beyond the prompt is left to the AI to figure out.

## Step 2 — Question deployed; candidate takes the test

The candidate writes a response.

## Step 3 — AI marking (black box)

The AI is given the question and the response. It does **all** the interpretive work:

- **Interprets the task** — works out what the question is asking the candidate to address.
- **Decides what "achievement" means** — judges whether the response addressed it, with no fixed yes/no checks.
- **Decides what "quality" means** — judges depth and development with no fixed ladder.

The AI returns a score. There is no rubric pinning it down, no evidence requirement, no per-rung definition.

## Result — score varies

Because every interpretive decision is the AI's own, scores wobble run to run. The same essay can score 80 on Monday and 65 on Tuesday. Two AI models will disagree. Calibration drifts as models update.

---

## Visual flow

```
┌──────────────────────────────────┐
│  STEP 1 — Question created        │
│                                   │
│  • prompt only                    │
│  • no task requirements           │
│  • no quality measures            │
└──────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────┐
│  STEP 2 — Question deployed       │
│  → Candidate takes the test       │
│  → Student response captured      │
└──────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────┐
│  STEP 3 — AI marking (black box)  │
│                                   │
│  AI interprets the task           │
│  AI decides what "achieve" means  │
│  AI decides what "quality" is     │
│                                   │
│  → no fixed checks                │
│  → no fixed ladder                │
│  → no evidence requirement        │
└──────────────────────────────────┘
                │
                ▼
        ┌────────────────────┐
        │   SCORE (varies)    │
        │   wobbles run-to-run│
        └────────────────────┘
```
