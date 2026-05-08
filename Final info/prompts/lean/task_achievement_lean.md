# Task Achievement Prompt (TA) — LEAN

Score task achievement. Return JSON only.

Task: {TASK_PROMPT}
Requirements: {TASK_REQUIREMENTS}
Task type checks: {TASK_TYPE_REQUIREMENTS}
CEFR: {QUESTION_CEFR_LEVEL}
Response: {STUDENT_RESPONSE}

If requirements or task type checks are empty or missing:
  return { "error": "missing_requirements", "task_achievement": null }

## PASS test

For each requirement (and each task type check), mark PASS or FAIL.

PASS = the response contains a sentence that BOTH:
  1. names what the requirement asks about, AND
  2. gives at least one specific detail (name, place, time, number, reason, example).

Otherwise FAIL. A bare topic mention with no specific detail is FAIL.

## Examples

- "I wake up at 6:30 and have toast." → PASS (action + time + food)
- "I do many things in the morning." → FAIL (no specific detail)
- "I like it because it helps me relax." → PASS (reason)
- "I like it a lot." → FAIL (no reason)
- "Last weekend we went to Lake Como." → PASS (named place)
- "We went to a beautiful place." → FAIL (no name)

## Calculation

  passes = total PASS count across requirements + task type checks
  total  = number of requirements + number of task type checks
  score  = round((passes / total) * 100), clamp 0-100

## Return

{
  "checks": [
    { "requirement": "...", "result": "PASS" or "FAIL" }
  ],
  "task_achievement": NUMBER
}
