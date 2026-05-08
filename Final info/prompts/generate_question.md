# Generate Question (AI authoring prompt)

Given a CEFR level, task type, and topic, generate a level-appropriate
question stem that the student will see when answering.

The stem must contain 3 bullet points. Those bullets will be turned
into task requirements by the next step (`generate_task_requirements.md`).

---

## Inputs

CEFR LEVEL: {CEFR_LEVEL}     (one of: A1, A2, B1, B2, C1)
TASK TYPE: {TASK_TYPE}        (one of: email, letter, paragraph, article, essay, report, proposal, summary)
TOPIC: {TOPIC}                 (short topic label, e.g., "workplace and jobs")

## Rules

1. **Output a question stem with this structure:**
   - **Framing line:** 1 short sentence introducing the topic.
   - **Instruction line:** 1 short sentence telling the student what to write.
   - **3 bullet points:** what they must address.

2. **Always 3 bullet points.** Not 2, not 4. These are the seeds for
   task requirements; the next step expects exactly 3.

3. **Each bullet is a short concrete topic, 4–12 words.**
   Stem bullets may use a candidate-facing framing such as "Think about..."
   or "Consider..." (these are common in real exam prompts and are fine
   here). The underlying topic must still be a concrete noun phrase from
   which a clean task requirement can be drawn (e.g., bullet "Think about
   how technology has changed the workplace" → requirement "How technology
   has changed the workplace").
   Avoid the interpretive verbs *discuss*, *explore*, *reflect on*,
   *evaluate* — they describe an abstract task rather than a concrete topic.

4. **Match CEFR level** in vocabulary and grammar:

| Level | Vocabulary             | Grammar features                              |
|-------|------------------------|------------------------------------------------|
| A1    | basic, common words    | present simple, basic plurals                  |
| A2    | familiar everyday      | + past simple, future plans, can/must          |
| B1    | gives opinions         | + present perfect, conditionals, comparison    |
| B2    | abstract topics ok     | + hypotheticals, modal speculation             |
| C1    | nuanced vocabulary     | + complex clauses, hedging, register shifts    |

The question stem itself should be readable at the student's level.
Don't write a B1 question with C1 vocabulary in the framing.

5. **Match task type conventions:**

| Task type | Conventional phrasing                              |
|-----------|----------------------------------------------------|
| essay     | "Write an essay discussing..."                     |
| email     | "Write an email to [person] about..."              |
| letter    | "Write a letter to [authority] to..."              |
| paragraph | "Write a paragraph about..."                       |
| article   | "Write an article for [magazine/blog]..."          |
| report    | "Write a report on..."                             |
| proposal  | "Write a proposal for..."                          |
| summary   | "Read the text below and summarise..."             |

For **email** and **letter**, the framing line should set up a real
situation (e.g., "Your friend has invited you to a party next weekend.").
For **summary**, the bullets describe what the summary should focus on,
not new content (and the actual source text must be supplied separately
by the question author — leave a `[SOURCE TEXT GOES HERE]` placeholder).

6. **Topic must be on-topic.** The framing sentence must relate
   directly to the supplied topic.

7. **Bullets must be answerable** — each bullet should naturally yield
   a paragraph of writing at the supplied CEFR level.

8. **Suggest `word_count_min` and `word_count_max`** based on level
   and task type:

| Level | Range          |
|-------|----------------|
| A1    | 25–80          |
| A2    | 40–120         |
| B1    | 50–300         |
| B2    | 100–400        |
| C1    | 150–500        |

Adjust down for short task types (email/letter): use the bottom half
of the range. Adjust up for report/essay/proposal at higher levels:
use the top half of the range.


9. **Same stem, different level bars.** The same question stem can be
   used at different CEFR levels. When this happens, the stem does not
   change — only the quality marker bars change downstream. Do not
   generate a new stem for each level.

## Anti-patterns (do NOT do)

| Bad                                      | Good                                        |
|------------------------------------------|---------------------------------------------|
| 4 bullets ("just one extra...")          | Always exactly 3                            |
| Bullets that overlap topics              | Each bullet covers a distinct angle         |
| Interpretive verb in a bullet            | Concrete topic noun phrase                  |
| C1-level vocabulary in a B1 question     | Match vocabulary to the level               |
| Multi-clause framing line                | Keep framing to 1 short sentence            |
| Bullet containing a question mark        | Bullets are noun phrases, not questions     |

## Worked examples

### Example 1 — B1 essay

INPUT:
CEFR LEVEL: B1
TASK TYPE: essay
TOPIC: media, arts, literature, and entertainment

OUTPUT:
{
  "question_stem": "Music is something most people enjoy in their daily lives.\n\nWrite an essay discussing the role of music in your life and how it affects you.\n\n- Think about when and why you listen to music\n- Consider how music can affect your mood and the way you feel\n- Use examples from your own experience and hobbies",
  "word_count_min": 50,
  "word_count_max": 300
}

### Example 2 — A2 email

INPUT:
CEFR LEVEL: A2
TASK TYPE: email
TOPIC: holidays, travel, and transportation

OUTPUT:
{
  "question_stem": "You went to a place last weekend with your family.\n\nWrite an email to your friend telling them about it.\n\n- Where you went\n- What you did there\n- What you liked most",
  "word_count_min": 40,
  "word_count_max": 120
}

### Example 3 — B2 article

INPUT:
CEFR LEVEL: B2
TASK TYPE: article
TOPIC: workplace and jobs

OUTPUT:
{
  "question_stem": "Many people now work remotely instead of going to an office.\n\nWrite an article for a careers blog about whether remote work helps or harms employees.\n\n- Effects on productivity and work-life balance\n- Impact on relationships with colleagues\n- Which workers or jobs benefit most",
  "word_count_min": 100,
  "word_count_max": 400
}

## Output format (JSON only, no commentary, no markdown fences)

{
  "question_stem": "Framing line.\n\nInstruction line.\n\n- Bullet 1\n- Bullet 2\n- Bullet 3",
  "word_count_min": NUMBER,
  "word_count_max": NUMBER
}

## Self-check before returning

- [ ] Question stem has framing + instruction + exactly 3 bullets
- [ ] Bullets are noun phrases (no question marks, no "discuss/consider")
- [ ] Vocabulary matches the supplied CEFR level
- [ ] Phrasing matches the task type convention
- [ ] Word count range matches the level + task type rules
- [ ] Topic is reflected in the framing
- [ ] No more than one short framing sentence
