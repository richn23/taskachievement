# Generate Task Requirements (AI authoring prompt)

Given a question stem, generate exactly **3 task requirements**.
These are the bullet points the scorer's TA prompt will mark PASS/FAIL on.

---

## Inputs

QUESTION STEM:
{QUESTION_STEM}

CEFR LEVEL: {CEFR_LEVEL}
TASK TYPE: {TASK_TYPE}
TOPIC: {TOPIC}

## Rules

1. **Always 3 requirements.** Not 2, not 4.
2. **Short noun phrase, 4–10 words each.** Do not write full sentences.
3. **Testable.** The scorer must be able to ask: "Can I quote a sentence
   that names this topic AND gives a specific detail (name, place, time,
   number, reason, example)?". If you can't imagine that test passing or
   failing cleanly, the requirement is too vague.
4. **Map to the question stem's bullets when present.** If the stem
   already has 3 bullet points (e.g., "Think about X, consider Y,
   include Z"), use them as-is or with light rephrasing. Do NOT invent
   new topics not implied by the stem.
5. **Distinct topics.** No two requirements should overlap.
6. **Plain language at the CEFR level.** No academic jargon, no
   abstract nouns where a concrete one works.
7. **Avoid interpretive verbs** like "discuss", "explore", "consider",
   "reflect on", "evaluate". Replace with concrete asks: "name", "give",
   "explain why", "compare", "describe".

## Anti-patterns (do NOT do these)

| Bad                                | Good                                          |
|------------------------------------|-----------------------------------------------|
| "Discuss the importance of X"      | "Why X matters in daily life"                 |
| "Explore both sides"               | "Arguments for and against X"                 |
| "Give your opinion on X"           | "Your opinion AND a reason for it"            |
| "Reflect on technology"            | "How technology has changed the workplace"    |
| "Consider the environment"         | "Effects of X on the environment"             |
| "Talk about your experience"       | "Personal example to support argument"        |

## Worked example

QUESTION STEM:
> Music is something most people enjoy in their daily lives.
> Write an essay discussing the role of music in your life.
> - Think about when and why you listen to music
> - Consider how music can affect your mood
> - Use examples from your own experience

OUTPUT:
{
  "task_requirements": [
    "When and why you listen to music",
    "How music affects your mood",
    "Personal example to support argument"
  ]
}

## Output format (JSON only, no commentary)

{
  "task_requirements": ["...", "...", "..."]
}
