# Intelligibility & Effect Prompt (IE) — LEAN

Judge intelligibility and communicative effect. Return JSON only.

STUDENT RESPONSE: {STUDENT_RESPONSE}

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

Use the full scale. Do not compress into 60-75.

## Independence

Score only clarity and communicative effect. Do NOT consider whether the
student answered the question, addressed requirements, or developed points.

## Return

{
  "intelligibility_effect_score": NUMBER,
  "reason": "one short sentence"
}
