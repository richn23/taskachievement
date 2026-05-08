# Rewrite Question Stem (AI authoring prompt)

Given an original question stem and 3 already-generated task requirements,
rewrite the stem into the standard format: **framing line + instruction
line + 3 bullets**.

The 3 bullets must reflect the 3 task requirements in candidate-facing
language. The student sees this stem in the test — they do NOT see the
task requirements directly.

---

## Inputs

ORIGINAL QUESTION STEM:
{ORIGINAL_STEM}

TASK REQUIREMENTS (3 entries, in order):
{TASK_REQUIREMENTS}

CEFR LEVEL: {CEFR_LEVEL}
TASK TYPE: {TASK_TYPE}
TOPIC: {TOPIC}

---

## Rules

1. **Output exactly this 3-part structure:**
   - **Framing line** (1 short sentence introducing the topic)
   - **Instruction line** (1 short sentence telling the student what to write)
   - **3 bullets** (one per task requirement, in the same order)

2. **Preserve the spirit AND breadth of the original stem.** If the
   original framed the topic broadly (e.g., "effects of technology on
   society"), keep it broad. Do NOT narrow it into specific
   sub-topics in the bullets (e.g., do not turn "effects on society"
   into "effects on communication" + "effects on workplace"). The
   bullets should be *angles* the candidate can use to address the
   broad question, not pre-prescribed sub-topics. The student should
   retain freedom of choice within the broad topic.

3. **Bullets are candidate-facing.** Use phrasing like:
   - "Think about ..."
   - "Consider ..."
   - "Include ..."
   - "Use examples from ..."

   Avoid academic verbs ("discuss", "analyse", "evaluate") — these belong
   in the instruction line, not the bullets.

4. **Each bullet maps 1:1 to a task requirement.** Same order. Same topic.
   The bullet is the candidate-facing rewording; the task requirement is
   the scorer-facing PASS/FAIL gate.

5. **Match CEFR level** in vocabulary and grammar:

| Level | Vocabulary             | Grammar features                              |
|-------|------------------------|-----------------------------------------------|
| A1    | basic, common words    | present simple, basic plurals                 |
| A2    | familiar everyday      | + past simple, future plans, can/must         |
| B1    | gives opinions         | + present perfect, conditionals, comparison   |
| B2    | abstract topics ok     | + hypotheticals, modal speculation            |
| C1    | nuanced vocabulary     | + complex clauses, hedging, register shifts   |

6. **Match task type conventions** in the instruction line:

| Task type | Conventional phrasing                          |
|-----------|------------------------------------------------|
| essay     | "Write an essay discussing..."                 |
| email     | "Write an email to [person] about..."          |
| letter    | "Write a letter to [authority] to..."          |
| paragraph | "Write a paragraph about..."                   |
| article   | "Write an article for [magazine/blog]..."      |
| report    | "Write a report on..."                         |
| proposal  | "Write a proposal for..."                      |
| summary   | "Read the text below and summarise..."         |

7. **Do NOT add new content** beyond what the original stem and task
   requirements imply. If the original stem was vague, keep it vague —
   don't fabricate context the student then has to address.

## Anti-patterns (do NOT do)

| Bad                                              | Good                                          |
|--------------------------------------------------|-----------------------------------------------|
| Bullets that don't match the 3 task requirements | Bullets in 1:1 order with the requirements   |
| 4 bullets ("just one extra...")                  | Always exactly 3                              |
| Interpretive verbs in bullets (discuss, analyse) | Concrete asks ("Think about...", "Include...") |
| Adding a 4th topic the original didn't mention   | Stick to the original's scope                 |
| Rewriting the topic completely                   | Preserve the original framing                 |
| Bullet containing a question mark                | Bullets are noun phrases, not questions       |

## Worked example

INPUT:
ORIGINAL STEM: "How Work and Jobs have changed. The way people work today
has greatly changed from the past as a result of technological inventions."

TASK REQUIREMENTS:
1. How technology has changed the workplace
2. Benefits of these changes
3. Challenges these changes bring

CEFR: B1, TASK TYPE: essay, TOPIC: workplace and jobs

OUTPUT:
{
  "question_stem": "The way people work today has changed greatly because of technology.\n\nWrite an essay about how work and jobs are different today compared to the past.\n\n- Think about how technology has changed the workplace\n- Consider the benefits of these changes\n- Include the challenges these changes bring"
}

## Output format (JSON only, no commentary, no markdown fences)

{
  "question_stem": "Framing line.\n\nInstruction line.\n\n- Bullet 1\n- Bullet 2\n- Bullet 3"
}

## Self-check before returning

- [ ] Stem has framing + instruction + exactly 3 bullets
- [ ] Each bullet maps 1:1 to a task requirement (same order)
- [ ] Vocabulary matches the supplied CEFR level
- [ ] Instruction line matches the task type convention
- [ ] Original framing is preserved (no new topics added)
- [ ] Bullets use candidate-facing language ("Think about...", "Consider...", "Include...")
- [ ] No bullet uses interpretive verbs (discuss, analyse, evaluate)
- [ ] No question marks in bullets
