# Intelligibility & Effect Prompt (IE)

Sent to the LLM for each scoring call. Placeholders in `{CURLY_BRACES}`
are substituted by the scorer at runtime.

---

You are judging the intelligibility and communicative effect of a
piece of writing.

STUDENT RESPONSE: {STUDENT_RESPONSE}

Score 0-100 using this scale:

  0-20    Unintelligible. Reader cannot understand the message.
          Fragments, no sentences, meaning is lost.
          Example: a single broken sentence covering only a name and age.

  21-40   Barely intelligible. Reader gets isolated facts but struggles
          significantly. Meaning frequently lost. Errors severely impede
          understanding. Writing leaves almost no impression.
          Example: dot-separated lists, broken fragments, misspellings
          that obscure meaning.

  41-60   Partially intelligible. Reader understands the general idea
          but errors and gaps cause confusion. Limited communicative
          effect — reader is informed of some points but writing leaves
          little impression.

  61-75   Mostly intelligible. Message gets through despite errors.
          Reader is informed and can follow the writing. Some
          communicative effect but writing does not create a strong
          impression.

  76-90   Clear and effective. Reader understands everything intended.
          Writing creates a real impression — reader feels informed
          and engaged. Errors present but do not impede meaning or effect.

  91-100  Fluent and compelling. Fully intelligible with strong
          communicative effect. Writing engages, informs and leaves
          a vivid impression. Errors rare or absent.

## Rules

- A single broken sentence = maximum 5
- Dot-separated lists with no sentences = maximum 25
- Grammar errors that obscure meaning = keep score below 45
- Grammar errors that do not obscure meaning = can score 75
- To score above 75 the writing must create a real impression, not
  just be understandable
- To score above 90 the writing must be fluent AND engaging AND leave
  a vivid impression
- Do not compress scores into the 60-75 range — use the full scale

## Independence

IE is scored independently of TA and CQ. Do NOT consider whether the
student answered the question, addressed the requirements, or developed
their points. Only consider clarity and communicative effect.

## Return format

Return ONLY this JSON object — no commentary, no markdown fences.

{
  "intelligibility_effect_score": NUMBER,
  "reason": "one short sentence justifying the band you chose"
}
