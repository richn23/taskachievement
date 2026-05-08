# Dev Team Brief — AZE Writing Scorer Rebuild

## 1. Problem

The current writing scorer gives the AI too much freedom. At the moment, the AI decides:

- what the question is asking
- what counts as task achievement
- what counts as content quality

Because these criteria are not fixed, scores can vary between runs, between models, and after model updates. Example: the same essay may score 80 in one run and 65 in another.

## 2. Solution

We will move the scoring criteria into the Question Bank. Each writing question will include:

- fixed task requirements
- fixed content quality ladders
- a task type used to apply format checks

The AI will no longer invent the rubric. It will apply the rubric supplied by the Academic team.

The AI scorer will:

- check Task Achievement using PASS/FAIL checks
- score Content Quality using the supplied 0–3 ladders
- score Intelligibility & Effect using the existing banded scale (rolled into TA — see below)

**Final outputs are TA and CQ only.** Intelligibility & Effect (IE) is an *input* to the TA calculation, not a separate final score. TA and CQ are the only two values that feed into the existing scoring system.

Mental model:
- **TA = coverage + structure + communication (IE)**
- **CQ = depth and development**

## 3. Scope

**Included**

- Add new rubric metadata to writing questions
- Add task type format checks
- Replace TA and CQ scoring prompts
- Add authoring prompts for Academic team question creation
- Show TA and CQ as final scores; surface IE, PASS/FAIL checks and evidence quotes for transparency only

**Not included**

- No changes to existing recorded metrics
- No changes to dimension weighting configuration
- No changes to the candidate-facing test experience yet

---

## Priority 1 — Schema additions

Add three fields to each writing question:

```json
{
  "task_type": "essay",
  "task_requirements": [
    "Requirement 1",
    "Requirement 2",
    "Requirement 3",
    "Additional on-topic development"
  ],
  "development_markers": [
    {
      "requirement": "Requirement 1",
      "1_mentioned": "Topic named with no further detail",
      "2_developed": "Topic named AND a reason or how/why",
      "3_extended": "All of 2 AND a concrete specific example"
    }
  ]
}
```

Score 0 is implicit — if the AI cannot quote a sentence that addresses the requirement, it scores 0 and does not apply the ladder.

Also create a fixed lookup table for task type checks. Each task type defines 2–3 binary format checks specific to that genre (e.g., essay = clear position + supporting reasons + conclusion; email = clear message + addresses situation + responds to all parts). Full lookup lives in `config/task_type_requirements.json`. Task types covered:

- essay
- email
- letter
- paragraph
- article
- report
- proposal
- summary

Existing questions need a one-off migration to populate `task_requirements` and `development_markers`.

## Priority 2 — Scoring prompts

The scorer runs three independent prompts per response. Their outputs combine into **two final scores** (TA and CQ) — IE is rolled into TA.

1. **`task_achievement.md`** — Checks `task_requirements` + task type format checks. Output: PASS/FAIL per requirement/check.
2. **`intelligibility_effect.md`** — Scores communication effect on a 0–100 banded scale. **Output is an input to TA, not a separate final score.**
3. **`content_quality.md`** — Scores each task requirement against its supplied 0–3 ladder. Output: score + evidence quote per requirement.

The three calls can run in parallel. Outputs are then combined:

- **TA** = combination of `task_requirements` PASS rate + `task_type_checks` PASS rate + `intelligibility_effect_score`. The 80/20 weighting (binary checks vs IE) lives in the TA prompt logic.
  - **`task_type_checks` contribute to `task_requirement_score` via PASS/FAIL evaluation, but are not used as a separate weighted component in the final TA calculation.** `task_type_score` is shown in the per-response JSON for transparency only. Do not introduce a separate weight for it.
- **CQ** = sum of 0–3 scores across the 4 development markers, normalised to 0–100.

Final outputs only:

- Store and return: `task_achievement`, `content_quality`
- Do NOT create or expose: a separate IE final score, combined scores, or alternative aggregates
- IE remains visible in the per-response JSON (`intelligibility_effect_score`) for transparency and debugging, but it is not an output of the scoring pipeline

## Priority 3 — Authoring prompts

Add three Academic-team generation prompts to the question authoring screen. Each output feeds the next step:

1. **`generate_question.md`**
   Input: CEFR level, task type, topic
   Output: question stem, instruction, 3 bullets, word count range
2. **`generate_task_requirements.md`**
   Input: question stem + metadata
   Output: 4 task requirements (3 question-specific + 1 generic "Additional on-topic development")
3. **`generate_quality_markers.md`**
   Input: task requirements + metadata
   Output: 0–3 content quality ladder for each requirement

UI buttons needed:

- Generate Question
- Generate Task Requirements
- Generate Quality Markers

Results display should show:

- TA score (final)
- CQ score (final)
- IE score (transparency only — not a final output)
- per-requirement evidence quotes
- PASS/FAIL checks for transparency

---

## Appendix A — Validation rules (hard)

The scorer MUST validate every AI response against these rules. If any fail, the response is invalid and must be rejected or re-run.

### Array lengths

- `task_checks` length = 4
- `task_type_checks` length = 3
- `cq_scores` length = 4

### Allowed values for `result`

- `"PASS"` or `"FAIL"` — uppercase strings only
- No lowercase, no booleans, no alternative values

### Evidence rules — task checks (`task_checks`, `task_type_checks`)

- If `result` = `"PASS"` → `evidence` MUST contain a direct quote from the response (non-empty string)
- If `result` = `"FAIL"` → `evidence` MUST be an empty string `""`

### Evidence rules — CQ (`cq_scores`)

- If `score` = 0 → `evidence` MUST be an empty array `[]`
- If `score` ≥ 1 → `evidence` MUST contain at least one quoted string

### No-double-counting

- `cq_evidence_duplicates` MUST be an empty array `[]` on a valid response. Any sentence appearing as evidence under more than one requirement is a validation failure.

---

## Appendix B — Example scorer output

Sample JSON returned by the scoring pipeline for one candidate response. Illustrates field names and shape — useful for the dev team when wiring up storage, the results UI, and any downstream report generation.

```json
{
  "sample_num": 1,
  "response": "I listen to music every morning...",
  "word_count": 144,
  "word_count_compliance": 82,
  "task_requirement_score": 75,
  "task_type_score": 67,
  "intelligibility_effect_score": 68,
  "intelligibility_effect_reason": "Mostly clear with some grammar slips.",
  "task_achievement": 78,
  "content_quality": 67,
  "task_checks": [
    {
      "requirement": "When and why you listen to music",
      "result": "PASS",
      "evidence": "I listen on the bus to relax."
    },
    {
      "requirement": "What type of music you like",
      "result": "PASS",
      "evidence": "I like pop music because it is energetic."
    },
    {
      "requirement": "How often you listen to music",
      "result": "FAIL",
      "evidence": ""
    },
    {
      "requirement": "Additional on-topic development",
      "result": "PASS",
      "evidence": "Sometimes I share music with my friends."
    }
  ],
  "task_type_checks": [
    {
      "requirement": "Clear position",
      "result": "PASS",
      "evidence": "In my opinion, music is important..."
    },
    {
      "requirement": "Supporting reasons",
      "result": "PASS",
      "evidence": "It helps me relax and focus."
    },
    {
      "requirement": "Conclusion",
      "result": "FAIL",
      "evidence": ""
    }
  ],
  "cq_scores": [
    {
      "requirement": "When and why you listen to music",
      "score": 2,
      "evidence": ["I listen on the bus to relax."],
      "reason": "Names a time and reason but no concrete specific."
    },
    {
      "requirement": "What type of music you like",
      "score": 2,
      "evidence": ["I like pop music because it is energetic."],
      "reason": "Gives preference with basic reason."
    },
    {
      "requirement": "How often you listen to music",
      "score": 0,
      "evidence": [],
      "reason": "Not addressed."
    },
    {
      "requirement": "Additional on-topic development",
      "score": 1,
      "evidence": ["Sometimes I share music with my friends."],
      "reason": "Additional idea mentioned without development."
    }
  ],
  "cq_evidence_duplicates": [],
  "error": null
}
```
