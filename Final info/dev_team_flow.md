# AZE Writing Scorer — End-to-end flow (for dev team)

A simple three-step picture of how a question goes from authoring to a candidate's score.

## Step 1 — Academic team creates the question

Academic department uses the question-authoring UI to create a new question. They specify:
- **Question stem** — the prompt the candidate will see
- **Task requirements** — 3 things the candidate must address
- **Content Quality measures** — the 1/2/3 scoring ladders for each requirement (4 ladders total: 3 specific + 1 generic)
- **Metadata** — CEFR level, task type, topic, word count range

The completed question is saved to the **Question Bank**.

## Step 2 — Question deployed; candidate takes the test

The platform pulls the question from the Question Bank and serves it to the candidate. The candidate writes a response. The response is captured.

## Step 3 — AI marking (two dimensions)

### Task Achievement (TA) — 80 / 20 split
- **80% — binary checks (yes/no)**
  - Binary check on each *task requirement*
  - Binary check on each *task type requirement*
- **20% — Intelligibility & Effect (AI judgement, banded 0–100)**

### Content Quality (CQ)
- **0–3 ladder per task requirement** plus the generic 4th
- Scored against the question's CQ measures from the Question Bank
- Evidence-first: AI must quote the response sentence that matches each rung

## Step 4 — Scores feed the broader scoring system

TA and CQ are added to the existing metrics the platform already records (as per the previous system). The candidate's final result is produced by combining all metrics — not by TA and CQ alone.

---

## Main differences vs the previous system

- **Academic team provides more detail in the writing question for the AI** — explicit task requirements and quality measures, instead of a prompt the AI has to interpret.
- **AI now measures Task Achievement against consistent markers** — fixed yes/no checks per requirement, not a free-form judgement.
- **Each task type has specific requirements** — essay, email, letter, paragraph, article, report, proposal, summary all have their own format checks.
- **Content Quality is marked against a scale in the question management** — the scale lives with the question and varies by question, so the AI scores against a rubric the academic team owns, not against its own opinion.

---

## Visual flow

```
┌──────────────────────────────────┐
│  STEP 1 — Academic team           │
│  creates the question             │
│                                   │
│  • question stem                  │
│  • 3 task requirements            │
│  • 4 quality markers (1/2/3)      │
│  • CEFR / task type / topic       │
└──────────────────────────────────┘
                │
                ▼
        ╔══════════════╗
        ║ Question     ║
        ║ Bank         ║
        ╚══════════════╝
                │
                ▼
┌──────────────────────────────────┐
│  STEP 2 — Question deployed       │
│  → Candidate takes the test       │
│  → Student response captured      │
└──────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────┐
│  STEP 3 — AI marking (two dimensions)             │
│                                                   │
│  ┌─────────────────────────┬───────────────────┐  │
│  │  TASK ACHIEVEMENT       │ CONTENT QUALITY   │  │
│  │  (80 / 20 split)        │                   │  │
│  │                         │ • 0–3 ladder      │  │
│  │  80%  binary checks     │   per task req    │  │
│  │   ─ each task req       │ • Against CQ      │  │
│  │   ─ each task type req  │   measures from   │  │
│  │                         │   Question Bank   │  │
│  │  20%  Intelligibility   │ • Evidence-first  │  │
│  │       & Effect          │                   │  │
│  └─────────────────────────┴───────────────────┘  │
│                                                   │
└──────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────┐
│  STEP 4 — Combine with broader system     │
│                                           │
│  TA + CQ added to the platform's other    │
│  metrics → final candidate result         │
└──────────────────────────────────────────┘

╔════════════════════════════════════════════════╗
║  MAIN DIFFERENCES vs the previous system       ║
║                                                ║
║  • Academic team provides more detail in the   ║
║    writing question for AI                     ║
║  • AI now measures Task Achievement against    ║
║    consistent markers                          ║
║  • Each task type has specific requirements    ║
║  • Content Quality marked against a scale in   ║
║    the question management (varies by question)║
╚════════════════════════════════════════════════╝
```
