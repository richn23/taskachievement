# Content Quality Prompt (CQ)

Sent to the LLM for each scoring call. Placeholders in `{CURLY_BRACES}`
are substituted by the scorer at runtime.

The `{DEVELOPMENT_MARKERS}` payload comes directly from
`config/question_markers.json` for the question. It must include
4 requirements: 3 question-specific + 1 generic "Additional on-topic
development" (see question_creation_rules.md).

---

Score content quality for this response. Return JSON only.

Task: {TASK_PROMPT}
Task requirements with development ladders: {DEVELOPMENT_MARKERS}
Question CEFR level: {QUESTION_CEFR_LEVEL}
Response: {STUDENT_RESPONSE}

If DEVELOPMENT_MARKERS are empty or missing:
  return { "error": "missing_markers", "content_quality": null }

Note: Content Quality scores task requirements only. Task type format
requirements are handled by Task Achievement. Do not score format
requirements here.

## CRITICAL RULE — explicit-only

A requirement is only present in the response if a sentence
**explicitly and unambiguously** addresses it.

- Implications, "this could mean...", topic-adjacent content,
  things you can infer — these do NOT satisfy the requirement.
- If you cannot quote a sentence that clearly matches the
  requirement, the requirement is **absent**. Score 0.
- If a sentence sits between two rungs, choose the LOWER rung.
- This rule applies to all requirements, including the 4th.
- Do not let general impressions of essay quality, length, or
  topic relevance influence whether a requirement is present.

## CRITICAL RULE — language concreteness, not factual knowledge

CQ rewards **language proficiency**, not world knowledge.

A "concrete specific" in rung 3 can be ANY of:
- a personal anecdote with specific detail
- a developed hypothetical scenario
- a real-world reference (event, person, place, programme)
- a generic concept developed with concrete sub-categories

A student does NOT have to know specific historical events, news
stories, or named institutions to reach rung 3. A vivid hypothetical
with concrete language scores the same as a real-world citation.

What does NOT count as concrete:
- Generic statements ("it is good", "many people")
- Vague quantifiers ("a lot", "most", "some")
- Adjective-only descriptions ("a beautiful place")
- Bare topic mentions with no elaboration

## Ignore writing quality

CQ measures idea development only. Do not let grammar errors, spelling,
sentence structure, register, or writing quality influence any CQ
score. Those are scored under IE. A poorly written but well-developed
answer should score the same on CQ as a polished one with the same
ideas.

## How to score each requirement — evidence first, then rung

You MUST follow these steps in order. Do not score from a holistic
impression of the response.

**Step 1 — Extract evidence.**
Find sentences in the response that explicitly and unambiguously
address this requirement. Quote them verbatim into the `evidence` field.

- A sentence about a different requirement does NOT count as evidence
  for this one.
- The same sentence may serve as evidence for at most one requirement.
  If a sentence could plausibly fit two requirements, assign it to
  the one it most directly addresses; do not use it twice.

**Step 2 — Score from the evidence.**

- If `evidence` is empty: score **0**. Reason: "absent".
- If `evidence` exists, compare ONLY the quoted text against the
  3 rungs supplied for that requirement:

  1 = mentioned  — evidence matches the rung-1 description
  2 = developed  — evidence matches the rung-2 description
  3 = extended   — evidence matches the rung-3 description

- If between two rungs, choose the LOWER rung.
- A reason or example only counts if it is **concretely specific**
  in any of the four senses above (personal / hypothetical / real /
  developed-generic). Generic statements do not count.


## Special rule for the 4th requirement (Additional on-topic development)

The 4th requirement only credits content that is **semantically distinct**
from the other three requirements.

- If the "extra" content paraphrases or repeats an idea you already
  credited under another requirement, score the 4th requirement **0**.
  Distinct means semantically distinct, not lexically distinct.
- The extra point must add something new to the argument — a different
  angle, a new sub-topic within the question's subject, or a related
  consequence.
- Length alone does not count. A long essay that elaborates the same
  three points repeatedly should score 0 on the 4th requirement.

This guard exists because students sometimes pad an essay with
rephrased versions of their main points. The 4th requirement is meant
to reward genuinely additional thinking, not waffle.

## Calculation

  total_score = sum of all 0-3 scores
  max_score   = number_of_requirements × 3
  CQ          = round((total_score / max_score) * 100), clamp 0-100

## Return format

Return ONLY this JSON object — no commentary, no markdown fences.

{
  "scores": [
    {
      "requirement": "...",
      "evidence": ["verbatim quote 1", "verbatim quote 2"],
      "score": 0-3,
      "reason": "one sentence: which rung the evidence matches, and why"
    }
  ],
  "content_quality": NUMBER
}

If a requirement has no evidence, return `"evidence": []` and `"score": 0`.
