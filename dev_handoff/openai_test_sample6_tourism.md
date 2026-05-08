# OpenAI Test — Sample 6 (Tourism)

Run each of the three prompts below in OpenAI Playground (or ChatGPT) using `gpt-4o`, temperature `0`, response_format JSON.

System message for all three:
> You are a strict English-writing scorer. Always return valid JSON only — no prose, no markdown fences.

---

## Prompt 1 — TASK ACHIEVEMENT

# Task Achievement Prompt (TA) — LEAN

Score task achievement. Return JSON only.

Task: Write a essay on the topic: holidays, travel, and transportation.
Requirements: ["Positive effects of tourism", "Negative effects of tourism", "Impact on local people, businesses, and environment", "Additional on-topic development"]
Task type checks: ["Clear position or main idea", "Supporting reasons given", "Some form of conclusion or final point"]
CEFR: b1
Response: Tourism is the act of moving from one place to another for tourist attractions.Tourism has contributed to revenue in our country,this is in form of foreign exhange and this has lead to the development of infrastracures like schools and hospitals.Creation of international relatioship which can provide support to our country.Through constraction of hotels and lodges,there is improves urbanisation like towns.Rebels enter uganda through tourist which lead to loss of people through bomb blasts.Tourists stay in uganda has caused intermarrages

## PASS test

For each requirement (and each task type check), mark PASS or FAIL.

PASS = the response contains a sentence that BOTH:
  1. names what the requirement asks about, AND
  2. gives at least one specific detail (name, place, time, number, reason, example).

Otherwise FAIL. A bare topic mention with no specific detail is FAIL.

## Calculation

  passes = total PASS count across requirements + task type checks
  total  = number of requirements + number of task type checks
  score  = round((passes / total) * 100), clamp 0-100

## Return

{
  "checks": [{ "requirement": "...", "result": "PASS" or "FAIL" }],
  "task_achievement": NUMBER
}


---

## Prompt 2 — INTELLIGIBILITY & EFFECT

# Intelligibility & Effect Prompt (IE) — LEAN

Judge intelligibility and communicative effect. Return JSON only.

STUDENT RESPONSE: Tourism is the act of moving from one place to another for tourist attractions.Tourism has contributed to revenue in our country,this is in form of foreign exhange and this has lead to the development of infrastracures like schools and hospitals.Creation of international relatioship which can provide support to our country.Through constraction of hotels and lodges,there is improves urbanisation like towns.Rebels enter uganda through tourist which lead to loss of people through bomb blasts.Tourists stay in uganda has caused intermarrages

## Score 0-100 by band

  0-20    Unintelligible. Reader cannot understand. Fragments, no sentences.
  21-40   Barely intelligible. Isolated facts only. Errors severely impede meaning.
  41-60   Partially intelligible. General idea comes through but errors cause confusion.
  61-75   Mostly intelligible. Message gets through. Some communicative effect, no strong impression.
  76-90   Clear and effective. Real impression. Errors do not impede meaning.
  91-100  Fluent and compelling. Engages, informs, leaves vivid impression.

## Hard rules

- Single broken sentence → max 5
- Dot-separated lists with no sentences → max 25
- Errors that obscure meaning → below 45
- Above 75 requires real impression, not just understandability
- Above 90 requires fluent AND engaging AND vivid

Use the full scale.

## Return

{ "intelligibility_effect_score": NUMBER, "reason": "one short sentence" }


---

## Prompt 3 — CONTENT QUALITY

# Content Quality Prompt (CQ) — LEAN

Score content quality. Return JSON only.

Task: Write a essay on the topic: holidays, travel, and transportation.
Markers (4 ladders): [
  {
    "requirement": "Positive effects of tourism",
    "1_mentioned": "names a positive effect with no detail (e.g., tourism brings jobs)",
    "2_developed": "names a positive effect AND explains who benefits or how (e.g., tourism brings jobs to hotels and restaurants)",
    "3_extended": "all of 2 AND a named place, sector, or number (e.g., in my city thousands work in tourism \u2014 hotels, restaurants and tour guides)"
  },
  {
    "requirement": "Negative effects of tourism",
    "1_mentioned": "names a negative effect with no detail (e.g., there is pollution)",
    "2_developed": "names a negative effect AND explains the impact (e.g., crowds make daily life harder for locals)",
    "3_extended": "all of 2 AND a named place, situation, or example (e.g., in Venice the canals are overcrowded and rents have doubled)"
  },
  {
    "requirement": "Impact on local people, businesses, and environment",
    "1_mentioned": "mentions only one of [people / businesses / environment]",
    "2_developed": "covers at least two of the three AND describes a specific impact for each",
    "3_extended": "covers all three AND each with a specific impact, named place, or example"
  },
  {
    "requirement": "Additional on-topic development",
    "1_mentioned": "introduces a DISTINCT extra on-topic point \u2014 not a rephrasing or repeat of any other requirement \u2014 within the question's subject, with no further detail",
    "2_developed": "introduces a distinct extra on-topic point AND develops it meaningfully (a real reason, cause, or effect \u2014 not just length)",
    "3_extended": "introduces a distinct extra on-topic point AND develops it AND supports it with a concrete specific that genuinely advances the argument"
  }
]
CEFR: b1
Response: Tourism is the act of moving from one place to another for tourist attractions.Tourism has contributed to revenue in our country,this is in form of foreign exhange and this has lead to the development of infrastracures like schools and hospitals.Creation of international relatioship which can provide support to our country.Through constraction of hotels and lodges,there is improves urbanisation like towns.Rebels enter uganda through tourist which lead to loss of people through bomb blasts.Tourists stay in uganda has caused intermarrages

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

Grammar, spelling, structure, register — none affect CQ.

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
    { "requirement": "...", "evidence": ["..."], "score": 0-3, "reason": "one sentence" }
  ],
  "content_quality": NUMBER
}

