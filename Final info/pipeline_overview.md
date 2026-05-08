# Question authoring pipeline

Three prompts work in sequence to produce a fully scored writing question.

## Step 1 — `generate_question.md`

Input: CEFR level, task type, topic
Output: question stem with framing line, instruction line, and exactly 3 bullet points + word count range

## Step 2 — `generate_task_requirements.md`

Input: question stem from Step 1 + CEFR level, task type, topic
Output: 3 task requirement labels used by the scorer for PASS/FAIL

## Step 3 — `generate_quality_markers.md`

Input: 3 task requirements from Step 2 + question stem, CEFR level, topic
Output: full 0–3 scoring rubric for each requirement + the generic 4th

## Important notes

- The same question stem can be reused at different CEFR levels — only the quality markers change, not the stem
- Step 3 output feeds directly into the scoring system as the Content Quality prompt
- Each step depends on the output of the previous step — do not skip steps
