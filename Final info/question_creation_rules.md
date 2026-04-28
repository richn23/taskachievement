# Question Creation Rules

How to write new questions for the AZE Writing Scorer.

Each question consists of:
- A **prompt** (the question shown to the student)
- **Task requirements** (3 bullet points the student must address)
- **Development markers** — 4 ladders:
  - 3 question-specific (one per task requirement)
  - 1 generic ("Additional on-topic development") — same on every question
- Metadata: ref, CEFR level, task type, topic, word range

Stored in `config/question_markers.json` keyed by ref.

## Golden rules

1. **Three task requirements.** Always 3, no more, no less.

2. **Four ladders in development_markers.** The 3 question-specific
   ladders + the generic 4th. Always 4 entries in the array.

3. **Each requirement must be observable, not interpretive.** Anything
   the model has to *judge* will wobble. Anything it can *check* will not.
   - Bad:  "Explain your reasons"
   - Good: "Names at least one reason AND supports it with a specific
           cause or example"

4. **Each requirement must demand explicit content.** The CQ scoring
   uses the explicit-only rule. If a student doesn't *say* something,
   the model is told not to infer it.

5. **Use NAMED in rung-3 wherever a name is required.** Spell out what
   does NOT count.
   - Bad:  "names a song or genre"
   - Good: "all of 2 AND a NAMED song title (e.g., 'Yesterday'),
           NAMED artist (Coldplay, Beyoncé), or real genre (gospel,
           amapiano, rock). Mood-based labels like 'spiritual songs'
           or 'motivational songs' do NOT count."

## Ladder structure

Every requirement gets a 1/2/3 ladder. **0** is implicit and means
the requirement is absent. The model never sees a "0" rung — it
scores 0 if there is no evidence.

| Rung | Meaning   | Pattern                                          |
|------|-----------|--------------------------------------------------|
| 1    | mentioned | names the topic, no detail                       |
| 2    | developed | names the topic AND adds a reason or how/why     |
| 3    | extended  | all of 2 AND a specific named example or detail  |

## The generic 4th requirement (verbatim — copy into every question)

Append this entry to the `development_markers` array of every question.
Same wording every time:

```json
{
  "requirement": "Additional on-topic development",
  "1_mentioned": "introduces one extra on-topic point not covered by the other requirements, with no further detail",
  "2_developed": "introduces an extra on-topic point AND develops it with a reason, cause, or effect",
  "3_extended": "introduces an extra on-topic point AND develops it AND supports it with a specific example or detail"
}
```

If your authoring tool can auto-insert it on save, do that. Otherwise
copy and paste it from this document.

## Worked example

Question (task prompt):
> Music is something most people enjoy in their daily lives.
> Write an essay discussing the role of music in your life.

Task requirements:
1. When and why you listen to music
2. How music affects your mood
3. Personal example to support argument

Development markers — note 4 entries (3 specific + 1 generic):

```json
[
  {
    "requirement": "When and why you listen to music",
    "1_mentioned": "says they listen to music with no specific time or reason",
    "2_developed": "names at least one specific time/situation AND a specific reason (e.g., I listen on the bus to work because it makes the commute pass faster)",
    "3_extended": "all of 2 AND a NAMED song title, NAMED artist, or real genre (Coldplay, 'Yesterday', amapiano, gospel, classical, rock). Mood-based or function-based labels like 'spiritual songs' or 'motivational songs' do NOT count."
  },
  {
    "requirement": "How music affects your mood",
    "1_mentioned": "states music affects mood with no specific change",
    "2_developed": "describes a specific mood change AND links it to a type of music (e.g., fast songs energise me; slow songs calm me)",
    "3_extended": "all of 2 AND a NAMED song, NAMED artist, or specific situation. Categorical descriptions like 'spiritual songs' or 'motivational songs' do NOT satisfy 'named song/artist'."
  },
  {
    "requirement": "Personal example to support argument",
    "1_mentioned": "vague reference to a personal music experience (e.g., I love music)",
    "2_developed": "a specific anecdote with at least one named song, occasion, or feeling",
    "3_extended": "a fully developed anecdote with NAMED music (actual title or artist), specific situation, AND emotional outcome. A description like 'a song I memorised' does NOT count as named music."
  },
  {
    "requirement": "Additional on-topic development",
    "1_mentioned": "introduces one extra on-topic point not covered by the other requirements, with no further detail",
    "2_developed": "introduces an extra on-topic point AND develops it with a reason, cause, or effect",
    "3_extended": "introduces an extra on-topic point AND develops it AND supports it with a specific example or detail"
  }
]
```

## Checklist before publishing a question

- [ ] Three task requirements
- [ ] Four ladders in `development_markers` (3 specific + 1 generic 4th)
- [ ] Each requirement is testable (can the model quote a sentence that
      unambiguously addresses it?)
- [ ] Each rung-3 spells out what counts as "named/specific" and what
      does NOT count
- [ ] No requirement asks the model to infer or interpret
- [ ] Word range is realistic for the CEFR level
- [ ] Topic and task type filled in correctly
- [ ] Test it: run 5 sample responses through the scorer 5 times each.
      Within-essay CQ range should average under 8. If higher, tighten
      the wobbly rung's wording.

## Example responses to test against

When introducing a new question, write 3 quick test responses:

1. **Strong** — covers all 3 requirements with named details. Should
   score CQ 80+ stably.
2. **Borderline** — addresses topics but with vague language. Should
   score CQ 40-60 stably.
3. **Weak** — fragmentary or off-topic. Should score CQ 0-20 stably.

If any of those scores wobbles by more than 8 points across 5 runs,
the ladder for that requirement needs tightening.
