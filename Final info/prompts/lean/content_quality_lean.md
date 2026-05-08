# Content Quality Prompt (CQ) — LEAN

Score content quality. Return JSON only.

Task: {TASK_PROMPT}
Markers (4 ladders): {DEVELOPMENT_MARKERS}
CEFR: {QUESTION_CEFR_LEVEL}
Response: {STUDENT_RESPONSE}

If markers are empty or missing:
  return { "error": "missing_markers", "content_quality": null }

## Hard rule — explicit only

A requirement is present ONLY if a sentence in the response **explicitly and
unambiguously** addresses it. Inference, "could mean", topic-adjacent content,
hidden meaning — none of these count. If you cannot quote a clear matching
sentence, score 0.

## Process — for each requirement, in order

**Step 1 — Extract evidence.**
Quote sentences that explicitly address THIS requirement, verbatim, into the
`evidence` array.
- A sentence about a different requirement is not evidence here.
- One sentence may serve as evidence for at most one requirement.
- **If a sentence has already been used as evidence for another requirement,
  it is not available for this one. If no other evidence exists, score 0.**

**Step 2 — Score from the evidence.**
- Empty `evidence` → score 0. Reason: "absent".
- Otherwise compare ONLY the quote against the supplied 1/2/3 rungs:
  - 1 = matches the rung-1 description (mentioned)
  - 2 = matches the rung-2 description (developed)
  - 3 = matches the rung-3 description (extended)
- Between two rungs → choose the LOWER rung.

A reason or example only counts as concretely specific if it names a person,
place, time, number, song, situation, or similar. Generic statements
("it is good", "many people") do not count.

## Ignore writing quality

Grammar, spelling, structure, register — none affect CQ. Those are scored
under IE. A messy but well-developed answer scores the same as a polished
one with the same ideas.

## 4th-requirement guard

The 4th marker ("Additional on-topic development") only credits content
**semantically distinct** from the other three. If the extra content
paraphrases an idea already credited under another requirement, score 0.

## Calculation

  total_score = sum of 0-3 scores
  max_score   = number_of_requirements * 3
  score       = round((total_score / max_score) * 100), clamp 0-100

## Return

{
  "scores": [
    {
      "requirement": "...",
      "evidence": ["verbatim quote", "..."],
      "score": 0-3,
      "reason": "one sentence"
    }
  ],
  "content_quality": NUMBER
}

If absent: `"evidence": []` and `"score": 0`.
