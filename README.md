# AZE Writing Scorer

Single-file browser app for scoring English writing samples on Task Achievement, Content Quality, and Intelligibility & Effect.

## Run

1. Open `scorer.html` in any modern browser.
2. Paste your OpenAI API key into the header field.
3. Pick one of the embedded questions on Step 2 and run scoring on a sample, or upload a 2-column CSV (`question_id,response`) for bulk scoring.

## Authoring

On Step 1 ("Create Question"), use the AI Assistant to generate a question stem, task requirements, and quality markers. Save to localStorage or export as CSV.

## Prompts

The scoring and authoring prompts live in `Final info/prompts/`. The 7 reference questions live in `Final info/config/question_markers.json`. Both are also embedded directly in `scorer.html` so the page works from `file://` without a server.

## Deploy

Static deploy. Drop `scorer.html` on Vercel / Netlify / GitHub Pages — no build step needed. Each user supplies their own OpenAI key (stored in localStorage).
