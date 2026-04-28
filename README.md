# AZE Writing Scorer

Single-file browser app for scoring English writing samples on Task Achievement, Content Quality, and Intelligibility & Effect. The OpenAI key lives on the server, not in the browser.

## Architecture

- `scorer.html` — the entire UI (HTML + CSS + JS in one file).
- `api/openai.js` — Vercel Serverless Function that proxies the browser to OpenAI Chat Completions using the `OPENAI_API_KEY` env var. The browser never sees the key.
- `vercel.json` — static deploy config.

The browser POSTs to `/api/openai` with a model + messages payload; the function adds the Authorization header and forwards to `https://api.openai.com/v1/chat/completions`.

## Run (deployed)

1. Open the deployed URL.
2. Pick a question on Step 2 and run scoring on a sample, or upload a 2-column CSV (`question_id,response`) for bulk scoring.

No key entry on the page — the key is held server-side.

## Deploy on Vercel

1. Import the repo at [vercel.com/new](https://vercel.com/new).
2. Framework preset: **Other**. Root: `./`. No build command. Output directory: `.` (already in `vercel.json`).
3. Add the env var: **Settings → Environment Variables**:
   - `OPENAI_API_KEY` = `sk-...` (Production, Preview, Development as you like)
   - Optional: `OPENAI_ALLOWED_MODELS` = `gpt-4o,gpt-4o-mini,gpt-4.1,gpt-4.1-mini` (overrides the default allowlist enforced by the proxy)
4. Deploy. Visit `<your-domain>/scorer.html`.

Or via the Vercel CLI:

```bash
vercel link
vercel env add OPENAI_API_KEY production
vercel --prod
```

## Protect your spend

Anyone who can reach the URL can spend your OpenAI quota. Recommended:

- **Vercel Deployment Protection** (dashboard → Settings → Deployment Protection): Vercel Authentication or Password Protection. No code changes; gates the whole site.
- The proxy enforces a model allowlist (default: `gpt-4o`, `gpt-4o-mini`, `gpt-4.1`, `gpt-4.1-mini`). Override with `OPENAI_ALLOWED_MODELS`.

## Local development

`scorer.html` calls `/api/openai`, which only exists on Vercel. To run locally:

```bash
vercel dev
```

…then open the URL Vercel prints. Opening `scorer.html` directly via `file://` will fail at scoring time (no proxy).

## Authoring

On Step 1 ("Create Question") use the AI Assistant to generate a question stem, task requirements, and quality markers. Save to localStorage or export as CSV.

## Prompts

The scoring and authoring prompts live in `Final info/prompts/`. The 7 reference questions live in `Final info/config/question_markers.json`. Both are also embedded directly in `scorer.html` so the UI loads without fetching them.
