# Generate Quality Markers (AI authoring prompt)

Given the 3 task requirements, generate the full `development_markers`
array. The output must contain **4 entries**: the 3 question-specific
ladders + the verbatim generic 4th.

---

## Inputs

TASK REQUIREMENTS (3 entries, in order):
{TASK_REQUIREMENTS}

QUESTION STEM (for context):
{QUESTION_STEM}

CEFR LEVEL: {CEFR_LEVEL}
TOPIC: {TOPIC}

## Rules

1. **Output 4 markers, in this order:**
   - The 3 task requirements (in same order as input)
   - The generic 4th: "Additional on-topic development"

2. **The generic 4th is verbatim.** Copy it from the bottom of this
   prompt. Do not modify any wording.

3. **Each ladder has 3 rungs (1, 2, 3).** Score 0 is implicit ("absent").

4. **Use this exact rung pattern:**
   - **1_mentioned** — names the topic, no further detail.
   - **2_developed** — names the topic AND adds a reason, cause, effect,
     or how/why explanation. **The bar at this rung scales with CEFR
     level — see calibration table below.**
   - **3_extended** — all of rung 2 AND a **concrete specific** that
     adds meaningful elaboration. **The bar at this rung also scales
     with CEFR level.**

## CRITICAL — what "concrete specific" means in rung 3

The rung-3 anchor is about **language concreteness**, NOT factual or
world knowledge. We are scoring language proficiency, not encyclopedic
recall.

**Any of the following count as a concrete specific:**

| Type                  | Example                                                 |
|-----------------------|---------------------------------------------------------|
| Personal anecdote     | "my colleague Anna saves 2 hours commute every day"     |
| Hypothetical scenario | "imagine a parent who can drop their child at school"   |
| Developed-generic     | "tourism creates jobs in hotels, restaurants, and tour guides" |
| Real-world reference  | "the EU ban on factory farming"                         |
| Personal observation  | "my own family started using delivery apps in 2020"     |

**A response should NOT need to know specific historical events,
news stories, or named institutions to reach rung 3.** A student
inventing a vivid hypothetical with concrete language is at the
same level as a student citing a real event.

**What does NOT count as a concrete specific:**

- Generic statements: "it is good", "many people", "in some places"
- Vague quantifiers: "a lot", "lots of", "many", "most"
- Topic-only mentions without elaboration
- Adjective-only descriptions: "a beautiful place", "a difficult job"

**Do NOT use the literal word "NAMED" in capitals in any rung.**
The previous version did, and the AI started demanding real-world
proper nouns (specific historical events, branded products) which
biased the scoring toward learners with cultural / news exposure.
Use "specific" or "concrete" instead.

5. **Every rung-3 MUST include a "do NOT count" anti-example.** Pick what
   the topic most often gets wrong from students. Phrase as
   *"...do NOT count"* or *"X does NOT satisfy the rung"*.

6. **Provide a concrete `(e.g., ...)` example in rung 2 and rung 3.**
   The example should match the topic, the CEFR level, and what a
   student at that level would plausibly write at that rung. **Mix
   personal, hypothetical, and real-world examples** so the model
   doesn't over-anchor on real-world specifics.


7. **Rung 2 must include a boundary example.** Every rung-2 descriptor
   must include a "this scores 2, not 3" boundary example. This should
   be a response that looks competent and on-topic but stops short of
   the rung-3 bar — the kind of answer a solid B2 writer produces. The
   boundary example must closely mirror realistic student writing, not
   an obvious failure. This anchors the middle rung and prevents the
   AI from jumping directly from 1 to 3.

   Format: after the `(e.g., ...)` example in rung 2, append
   `(scores 2, not 3 — lacks [specific missing element])`.

## CEFR-level rung calibration

The same ladder pattern (1 → mentioned, 2 → developed, 3 → extended)
applies to all levels, but **the bar at each rung scales with CEFR**:

| Level | Rung 2 — "developed" expects                                     | Rung 3 — "extended" expects                                                   |
|-------|-------------------------------------------------------------------|-------------------------------------------------------------------------------|
| A1    | one reason or one specific detail                                | a concrete specific (a person, place, time, or object the student can describe) |
| A2    | one reason linked with "because" / "so" / "but"                  | a concrete specific + a brief link or reason                                  |
| B1    | one reason AND a specific link or example                        | a concrete specific that develops the point with a clear example              |
| B2    | TWO distinct points OR a comparison (X vs Y) with explanation    | TWO concrete specifics that distinguish or categorise                         |
| C1    | evaluative reasoning, hedged generalisation, or a trade-off      | a concrete specific + counter-evidence, qualification, or evaluation          |

**Why level matters:** a B2 student writing "I went to Paris because it was
nice" should NOT score rung 3 — that's a B1-level answer. For B2, rung 3
should require categorisation (multiple specifics that group the reasons),
comparison, or qualification.

## Anti-example pattern by topic family

Match the rung-3 anti-example to the topic family:

| Topic family       | What "concrete specific" can include                  | What does NOT count                              |
|--------------------|-------------------------------------------------------|--------------------------------------------------|
| Music              | song title, artist, genre, or personal listening situation with detail | mood categories ("sad songs", "motivational music"), or naming two activities without explaining why music fits each one |
| Travel / places    | a place (real or personal), a journey detail          | "a beautiful place", "somewhere nice"            |
| Workplace          | role, tool, or specific task                          | "technology", "the workplace", "things"          |
| Food               | a dish, a meal, a brand, a personal cooking memory    | "good food", "tasty", "nice meals"               |
| People             | a person (real or hypothetical with detail)           | "someone", "people", role-only "my friend"       |
| Time               | a specific time, occasion, or year                    | "in the past", "long time ago"                   |
| Numbers / scale    | numbers, fractions, frequencies                       | "many", "most", "some", "a lot"                  |
| Government policy  | a programme, law, action, or local detail             | "the government should", "they need to"          |
| Environment        | an action, place, or observed habit                   | bare verbs ("recycling"), no agent               |
| Historical / world | a real event OR a hypothetical scenario               | demanding only real events; vague ("in history") |

**For "historical / world" topics, accept hypothetical scenarios just
as readily as real events.** A student writing a vivid hypothetical
("imagine two countries fighting over the same river…") at B2 should
score the same as one citing a real event.

## Worked examples

### B1 example (calibration baseline)

INPUT:
TASK REQUIREMENTS:
[
  "When and why you listen to music",
  "How music affects your mood",
  "Personal example to support argument"
]
CEFR LEVEL: B1

OUTPUT (rung 3 for first requirement):
"all of 2 AND a concrete specific — could be a song or artist
 (Coldplay, 'Yesterday'), a real genre (gospel, amapiano, classical),
 or a specific personal listening situation (e.g., on the bus to
 work, before a family dinner). Mood categories like 'spiritual songs'
 or 'motivational songs' do NOT count as concrete specifics."

### B2 example (note the extra demand at rung 3)

INPUT:
TASK REQUIREMENTS:
[
  "Reasons why people choose to travel"
]
CEFR LEVEL: B2

OUTPUT (rung 3):
"all of 2 AND TWO concrete specifics that distinguish the reasons.
 These can be real or personal or hypothetical (e.g., 'tourists go to
 a relaxing beach destination while professionals go to a major business
 city'; or 'in my family, my mother travels for cultural festivals while
 my brother travels for work conferences'). A single example with no
 comparison, or generic descriptors like 'a beautiful place', do NOT count."

### B2 example with a knowledge-heavy topic

INPUT:
TASK REQUIREMENTS:
[
  "Causes of war with specific examples"
]
CEFR LEVEL: B2

OUTPUT (rung 3):
"all of 2 AND a concrete specific cause that the student develops with
 detail — could be a real historical event (e.g., a known conflict the
 student remembers), a present-day situation (e.g., a current border
 dispute they have read about), OR a clearly developed hypothetical
 (e.g., 'if a country runs out of water, it might invade its neighbour
 to control the river'). Vague phrases like 'people fight for resources'
 with no specific cause or scenario do NOT count. **The student does
 NOT have to cite a particular historical event** — a developed
 hypothetical is equally valid."

### C1 example (rung 3 demands evaluation)

INPUT:
TASK REQUIREMENTS:
[
  "Effects of remote work on productivity"
]
CEFR LEVEL: C1

OUTPUT (rung 3):
"all of 2 AND a concrete specific + counter-evidence or trade-off
 (e.g., 'remote work helps office workers focus, but factory workers
 cannot benefit because their jobs need physical presence'; or a
 personal example with a balanced reflection). A single supportive
 example without nuance does NOT count at C1."

## Verbatim generic 4th marker (always include, never modify)

```json
{
  "requirement": "Additional on-topic development",
  "1_mentioned": "introduces a DISTINCT extra on-topic point — not a rephrasing or repeat of any other requirement — within the question's subject, with no further detail",
  "2_developed": "introduces a distinct extra on-topic point AND develops it meaningfully (a real reason, cause, or effect — not just length)",
  "3_extended": "introduces a distinct extra on-topic point AND develops it AND supports it with a concrete specific that genuinely advances the argument"
}
```

## Output format (JSON only, no commentary)

{
  "development_markers": [
    { "requirement": "...", "1_mentioned": "...", "2_developed": "...", "3_extended": "..." },
    { "requirement": "...", "1_mentioned": "...", "2_developed": "...", "3_extended": "..." },
    { "requirement": "...", "1_mentioned": "...", "2_developed": "...", "3_extended": "..." },
    { "requirement": "Additional on-topic development", "1_mentioned": "...", "2_developed": "...", "3_extended": "..." }
  ]
}

## Self-check before returning

- [ ] Exactly 4 markers
- [ ] Order: input requirement #1, #2, #3, then the generic 4th
- [ ] The 4th marker is byte-identical to the verbatim block
- [ ] No rung uses the literal word **NAMED** in capitals
- [ ] Every rung-3 says **"do NOT count"** with a topic-relevant anti-example
- [ ] Every rung-3 lists multiple anchor types (personal / hypothetical /
      real-world / developed-generic) — NOT a single specific real event
- [ ] Every rung-2 and rung-3 contains a concrete (e.g., …) example
- [ ] Rung-2 and rung-3 bars are calibrated to the supplied CEFR level
- [ ] Every rung-2 includes a boundary example showing what scores 2 but not 3
- [ ] Rung-2 boundary examples mirror realistic student writing, not obvious failures
- [ ] No rung uses interpretive verbs ("discuss", "explore", "reflect")
