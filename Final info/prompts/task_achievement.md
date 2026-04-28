# Task Achievement Prompt (TA)

Sent to the LLM for each scoring call. Placeholders in `{CURLY_BRACES}`
are substituted by the scorer at runtime.

---

Score task achievement for this response. Return JSON only.

Task: {TASK_PROMPT}
Task requirements: {TASK_REQUIREMENTS}
Task type requirements: {TASK_TYPE_REQUIREMENTS}
Question CEFR level: {QUESTION_CEFR_LEVEL}
Response: {STUDENT_RESPONSE}

If task_requirements or task_type_requirements are empty or missing:
  return { "error": "missing_requirements", "task_achievement": null }

## How to score each requirement

For each requirement in task_requirements and task_type_requirements,
mark it PASS or FAIL using this single test:

**PASS test (must satisfy BOTH):**
1. The response contains a sentence that names what the requirement asks about.
2. That sentence (or an adjacent one) gives at least ONE specific detail —
   a name, place, time, number, reason, or example.

If only condition 1 is met (named but no specific detail), mark FAIL.
If neither is met, mark FAIL.

A "mention" is naming the topic without a specific detail.
"Addressed" means named AND with at least one specific detail.

## Worked examples (apply this same standard)

Requirement: "what you do in the morning"
- "I wake up at 6:30 and have toast for breakfast." -> PASS
  (action named; specific time and specific food = details)
- "Every morning I run in the park near my house." -> PASS
  (action named; specific place = detail)
- "I do many things in the morning." -> FAIL
  (topic named; zero specific details)
- "Mornings are great." -> FAIL
  (no action named)

Requirement: "why you like it"
- "I like it because it helps me relax after work." -> PASS
  (reason given)
- "I like it a lot." -> FAIL
  (positive opinion only; no reason)
- "It is good and I enjoy it." -> FAIL
  (still no reason — 'good' is not a reason)

Requirement: "where you went"
- "Last weekend we went to Lake Como." -> PASS
  (specific place named)
- "We went to a beautiful place." -> FAIL
  (no specific place — 'beautiful place' is not a name or location)

Apply the same PASS test to every requirement, including the
task_type_requirements (e.g. "responds to all parts of the situation").

## Calculation

  passes = total number of PASS results
  total  = number of task_requirements + number of task_type_requirements
  score  = round((passes / total) * 100), clamp 0-100

## Return format

{
  "checks": [
    { "requirement": "...", "result": "PASS" },
    { "requirement": "...", "result": "FAIL" }
  ],
  "task_achievement": NUMBER
}
