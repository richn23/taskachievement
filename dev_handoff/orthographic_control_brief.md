# Implementation Brief: Orthographic Control Dimension (7th dimension)

**For:** Claude Code / Cursor
**Project:** scorer-arabic.html — Arabic writing scorer prototype
**Author:** Richard
**Date:** 2026-05-21
**Status:** Step 2 of a two-step build. Step 1 (Calibration tab) is complete and pushed.

---

## 1. Context

This is a single-file browser app for scoring Arabic writing samples. The previous build (Step 1) added a Calibration tab that lets the user enable/disable dimensions and tune weights. This step adds a new **7th dimension — Orthographic Control** — that scores Arabic-specific spelling and script correctness as a separate construct from grammar.

The full specification is in:

```
Final info/orthographic_control_spec_v1.1.md
```

**Read that spec before writing any code.** This brief tells you where to put things and how to wire them into the existing app. It does not restate the formulas — those live in the spec, and the worked example in §9 of the spec is the regression test for the deterministic scoring.

### Project root

```
C:\Users\richa\Desktop\TASK ACHIEVEMENt and CONTENT QUALITY\
```

### Files to know about

| File | Role | Action |
|------|------|--------|
| `scorer-arabic.html` | The app you are editing. ~4,600 lines after Step 1. | **Edit** |
| `Final info/orthographic_control_spec_v1.1.md` | The spec for the dimension you are building. | **Source of truth — read before coding.** |
| `Final info/config/` | Folder for curated error lists (does not yet exist). | **Create folder + 3 JSON files (see §5).** |
| `dev_handoff/calibration_tab_brief.md` | The Step 1 brief — useful for understanding the calibration data shape. | Read for context. |
| `api/openai.js` | Vercel serverless function proxying to OpenAI / Anthropic. | **No changes needed.** |
| `scorer.html` | English version — does not have this dimension. | **Reference only — do not edit.** |

### Existing state after Step 1

- 6 dimensions are scored. Dimension IDs: `task_achievement`, `content_quality`, `style_register`, `language_range`, `organisation_coherence`, `language_accuracy`.
- The Calibration tab is at `view-calibration` (sits between Scoring System and 1. Create Question).
- Calibration is persisted in `localStorage` under key `azescorer.arabic.calibration`.
- All scoring functions read the active config via `getCalibration()` and use `_dimEnabled(id)` and `_metricPct(dimId, metricId)` helpers to gate calls and weight outputs.
- The constant `_EW = 100 / 6` is the equal-weight per dimension at defaults. This needs to become `100 / 7` (see §7.4).

### Scoring tree for the new dimension

From the spec (§3):

```
Orthographic Control /100
 ├── Deterministic Orthography Score /100        (weight 0.60)
 │    ├── Technical Quality /100                  (weight 0.40)
 │    │    ├── Arabic Punctuation Usage /100
 │    │    ├── Whitespace & Formatting /100
 │    │    ├── Tatweel Abuse /100
 │    │    └── Non-Arabic Character Intrusion /100
 │    └── Common Error Detection /100             (weight 0.60)
 │         ├── Taa Marbuta Confusion /100
 │         ├── Alif Form Confusion /100
 │         └── Common Hamza Errors /100
 └── LLM Orthographic Accuracy /100               (weight 0.40)
```

---

## 2. What to build

1. A deterministic Arabic-orthography analyser in JS that returns the full breakdown per §5 of the spec.
2. Three curated-list JSON files under `Final info/config/`.
3. An LLM Orthographic Accuracy scorer (new prompt, new API call, parsed result).
4. Registration of the new dimension `orthographic_control` in `CALIB_DEFAULTS` and migration logic so users with an existing 6-dimension calibration in localStorage get the 7th added.
5. Wiring into `scoreSample()` so the dimension runs (gated by `_dimEnabled("orthographic_control")`) and contributes to the Overall Score.
6. UI display in the results panel matching the visual style of the existing 6 dimensions, including the flags list (mis-spellings + suggested corrections) and the LLM justification.

This step **does not change** any of the existing 6 dimensions. Regression: running with default calibration on any past sample must produce identical scores for the 6 existing dimensions and a new 7th score from Orthographic Control.

---

## 3. Dimension scope (do not violate)

Per spec §4: Orthographic Control evaluates Arabic spelling control, hamza usage, taa marbuta correctness, alif form correctness, script consistency, and technical cleanliness.

It **does NOT** evaluate grammar, syntax, vocabulary, task achievement, coherence, register, or content quality. The LLM prompt explicitly guards against leakage — see §6.

---

## 4. Minimum length floor

Below **10 words**, the dimension returns `N/A*` (per spec §7). This is lower than the system-wide 30-word floor because orthography reads meaningfully on very short responses where most other dimensions cannot.

When `N/A*` is returned, the dimension is excluded from Overall, and the weights of the remaining enabled valid dimensions are renormalised proportionally — exactly the same handling already implemented in `scoreSample()` for other short-response cases.

---

## 5. Curated lists

Create `Final info/config/` (folder does not exist yet) and add three JSON files. Initial seed contents below — these match the spec's §5.2 tables.

### 5.1 `Final info/config/orthography_taa_marbuta.json`

```json
{
  "version": "v1.0.0",
  "category": "taa_marbuta",
  "entries": [
    { "incorrect": "مدرسه", "correct": "مدرسة", "tier": "always_wrong", "added": "2026-05-21", "added_by": "richard" },
    { "incorrect": "حياه",  "correct": "حياة",  "tier": "always_wrong", "added": "2026-05-21", "added_by": "richard" },
    { "incorrect": "شجره",  "correct": "شجرة",  "tier": "always_wrong", "added": "2026-05-21", "added_by": "richard" },
    { "incorrect": "فكره",  "correct": "فكرة",  "tier": "always_wrong", "added": "2026-05-21", "added_by": "richard" },
    { "incorrect": "مكتبه", "correct": "مكتبة", "tier": "always_wrong", "added": "2026-05-21", "added_by": "richard" }
  ]
}
```

### 5.2 `Final info/config/orthography_alif.json`

```json
{
  "version": "v1.0.0",
  "category": "alif",
  "entries": [
    { "incorrect": "الى",  "correct": "إلى",  "tier": "always_wrong",  "added": "2026-05-21", "added_by": "richard" },
    { "incorrect": "حتي",  "correct": "حتى",  "tier": "always_wrong",  "added": "2026-05-21", "added_by": "richard" },
    { "incorrect": "علي",  "correct": "على",  "tier": "usually_wrong", "added": "2026-05-21", "added_by": "richard" },
    { "incorrect": "موسي", "correct": "موسى", "tier": "usually_wrong", "added": "2026-05-21", "added_by": "richard" }
  ]
}
```

Note: `علي` and `موسي` are tagged `usually_wrong` because they are also valid male names (Ali, Musa). The proper-noun gate (§5.3 of spec) protects them.

### 5.3 `Final info/config/orthography_hamza.json`

```json
{
  "version": "v1.0.0",
  "category": "hamza",
  "entries": [
    { "incorrect": "انت",     "correct": "أنت",      "tier": "always_wrong", "added": "2026-05-21", "added_by": "richard" },
    { "incorrect": "اخذ",     "correct": "أخذ",      "tier": "always_wrong", "added": "2026-05-21", "added_by": "richard" },
    { "incorrect": "مسئلة",   "correct": "مسألة",    "tier": "always_wrong", "added": "2026-05-21", "added_by": "richard" },
    { "incorrect": "اولاد",   "correct": "أولاد",    "tier": "always_wrong", "added": "2026-05-21", "added_by": "richard" },
    { "incorrect": "الاشجار", "correct": "الأشجار",  "tier": "always_wrong", "added": "2026-05-21", "added_by": "richard" },
    { "incorrect": "ان",      "correct": "أن",       "tier": "always_wrong", "added": "2026-05-21", "added_by": "richard" }
  ]
}
```

### 5.4 Loading approach

The browser cannot `fs.readFile` a JSON file at runtime from a static HTML page without fetch. Two acceptable options:

**Option A (preferred):** Inline the three lists as JS constants in `scorer-arabic.html` (e.g. `const ORTHOGRAPHY_TAA_MARBUTA = { ... }`), and also write the same JSON to `Final info/config/*.json` as the canonical source. The HTML file's copy is treated as a build snapshot. Add a comment banner above each inlined constant noting "synced from Final info/config/orthography_taa_marbuta.json (v1.0.0) on 2026-05-21".

**Option B:** Fetch the JSON files at app init via `fetch('Final info/config/orthography_taa_marbuta.json')`. Works on Vercel deploy, but adds an async dependency to startup and complicates local file:// testing.

Go with **Option A**. The list version string from the JSON file becomes the `version` field in the inlined object so reproducibility is preserved.

### 5.5 Proper-noun gate

Per spec §5.3, a `usually_wrong` candidate is suppressed when preceded by a title token: `السيد`, `الأستاذ`, `الدكتور`, `الشيخ`, `سيدي`, or when the candidate appears between Arabic or Latin quotation marks (`«…»`, `"…"`, `'…'`).

Implementation: when scanning tokens, check the previous non-whitespace token against the title set. For quoted-region detection, do a simple span-pair match across the response, mark quoted spans, and skip flagging on tokens inside them.

### 5.6 Dedup rule

Per spec §5.2.5: if the same misspelled form occurs multiple times, count it as **one unique error** for scoring, but record all occurrences in the output `flags` array.

---

## 6. Deterministic implementation

Add a top-level function:

```js
function computeArabicOrthography(response, options) {
  // options: { allow_loanword_list: [], titles: [...], list_versions: { ... } }
  // returns the deterministic-branch object shaped like spec §8 output schema
}
```

It should compute and return:

```js
{
  technical_quality: NUMBER,
  technical_quality_breakdown: {
    punctuation: NUMBER,
    whitespace: NUMBER,
    tatweel: NUMBER,
    non_arabic_intrusion: NUMBER
  },
  common_error_detection: NUMBER,
  common_error_detection_breakdown: {
    taa_marbuta: NUMBER,
    alif_forms: NUMBER,
    hamza: NUMBER
  },
  deterministic_orthography_score: NUMBER,
  flags: [ /* per spec §8 */ ],
  flags_summary: { /* per spec §8 */ },
  list_versions: { /* per spec §8 */ },
  letter_form_counts: { /* per spec §6.2 — used as LLM prompt context */ }
}
```

All formulas come from spec §5. Do not invent or smooth — match the spec precisely.

### 6.1 Formula references (do not paraphrase, use the spec)

- §5.1.1 Arabic Punctuation Usage
- §5.1.2 Whitespace & Formatting
- §5.1.3 Tatweel Abuse
- §5.1.4 Non-Arabic Character Intrusion
- §5.1.5 Technical Quality composite (mean of four)
- §5.2.4 Common Error Detection per-category formula (density × 8)
- §5.2.5 Dedup rule
- §5.2.6 Common Error Detection composite (mean of three)
- §5.3 False-positive policy (`always_wrong` = 1.0, `usually_wrong` = 0.5)
- §6.2 Letter-form counts table

### 6.2 Tokenisation

Words = whitespace-separated tokens after stripping punctuation. The same tokenisation used elsewhere in scorer-arabic for word counts should be used here. Arabic word boundary rules are simpler than e.g. Chinese — splitting on `/\s+/` after stripping punctuation is fine for V1.

### 6.3 Letter-form counts (for LLM context)

Compute counts per spec §6.2 by scanning Unicode code points:

| Key | Unicode |
|-----|---------|
| `alif` | U+0627 ا |
| `alif_hamza_above` | U+0623 أ |
| `alif_hamza_below` | U+0625 إ |
| `alif_madda` | U+0622 آ |
| `alif_maqsura` | U+0649 ى |
| `taa_marbuta` | U+0629 ة |
| `haa_final` | U+0647 ه appearing as final character of a word |
| `hamza_isolated` | U+0621 ء |
| `hamza_yaa` | U+0626 ئ |
| `hamza_waw` | U+0624 ؤ |

Plus `words: NUMBER`.

---

## 7. Calibration tab registration

This is where Step 2 differs from a vanilla "add a dimension" — the dimension must register itself in the existing calibration system.

### 7.1 Add to `CALIB_DEFAULTS`

In `scorer-arabic.html` around line 4372, the `CALIB_DEFAULTS` constant currently has 6 dimensions. Add a 7th. Flatten the OC scoring tree into **three sibling metrics** in the calibration UI — same pattern Step 1 used for Task Achievement (WCC / TA / IE).

```js
{
  id: "orthographic_control",
  label: "Orthographic Control",
  enabled: true,
  weight_pct: _EW,
  metrics: [
    { id: "technical_quality",        label: "Technical Quality (code)",       weight_pct: 24.0 },
    { id: "common_error_detection",   label: "Common Error Detection (code)",  weight_pct: 36.0 },
    { id: "llm_orthographic_accuracy",label: "LLM Orthographic Accuracy",      weight_pct: 40.0 }
  ]
}
```

These defaults (24 / 36 / 40) reproduce the spec's formula exactly:
- Deterministic × 0.60 split into Technical Quality (0.40) and Common Error Detection (0.60) → 24 and 36.
- LLM at 0.40 → 40.

This means default calibration produces the spec's worked example score, and the user can tune any of the three independently.

### 7.2 Update `_EW`

Change `const _EW = 100 / 6;` to `const _EW = 100 / 7;`.

Adjust the rounding-absorber dimension (currently `language_accuracy` gets `100 - 5 * _EW`) to absorb the new total: `100 - 6 * _EW`.

### 7.3 Migration for existing localStorage

Users who used Step 1 already have a 6-dimension config in localStorage under `azescorer.arabic.calibration`. On load, if the parsed config is schema-valid but has only 6 dimensions and no `orthographic_control` entry, **migrate it**:

1. Append the new dimension at the end of `dimensions` with `enabled: true` and `weight_pct: 100 / 7`.
2. Rescale the existing 6 dimensions' weights proportionally so they now sum to `6/7 × 100 ≈ 85.714`, leaving `1/7 ≈ 14.286` for the new one.
3. Save back to localStorage.
4. Do not silently overwrite the saved config with defaults — the user may have tuned weights and they should be preserved.

Implementation hint: add a `_migrateCalibIfNeeded(config)` function called inside `getCalibration()` right after schema validation succeeds.

### 7.4 Schema validation

`_isValidCalibSchema` currently requires `c.dimensions.length >= 6`. Keep that check — both 6-dim (old) and 7-dim (new) configs pass. The migration handles the 6 → 7 transition.

### 7.5 Inner-metric exposure

Per the calibration tab contract (Step 1, §4.3): **weights only — do not expose formula constants**. So the calibration tab exposes only the three sibling weights above. It does NOT expose:

- The density multipliers (8) in §5.2.4
- The substitution-penalty cap (40) in §5.1.1
- The punctuation density bands (5-20 / 0-5 / 20-40 / >40)
- The tatweel single-typo allowance (70)
- The tier penalty values (always_wrong = 1.0, usually_wrong = 0.5)

Those live in the code, change via spec revisions, and are out of scope for user tuning. (They become tunable in the calibration phase per spec §10 — that's a future spec change, not a UI change.)

---

## 8. LLM Orthographic Accuracy

### 8.1 Prompt design (anti-leakage)

Per spec §6.5, the prompt MUST include explicit examples that prevent grammar / vocabulary / coherence leakage. The exact phrasing from the spec is required (these examples are part of the construct definition):

- *"A response with bad verb conjugation but perfect hamza placement should score high on this metric."*
- *"A response that goes off-topic but spells everything correctly should score high on this metric."*
- *"A response written in dialect but with consistent orthographic conventions should score high on this metric. Dialect detection belongs to Style & Register, not here."*

### 8.2 Letter-form counts as context

The deterministic layer produces `letter_form_counts` (§6.3 of this brief, §6.2 of the spec). Inject this object into the prompt as a `<letter_form_counts>` XML block so the LLM can spot suspicious distributions (e.g. zero `ة` in 200 words of expository writing).

### 8.3 Output JSON contract

The LLM call returns:

```json
{
  "llm_orthographic_accuracy_score": NUMBER,
  "justification": "2-3 sentences. Quote 1-2 Arabic phrases from the response as evidence — of either accuracy or error. Stay strictly within orthography."
}
```

No extra keys. No markdown fences. `temperature: 0`. Use the same `callOpenAI` plumbing as the other dimensions; identifier `"ORTHO"`.

### 8.4 Short-response cap

Per spec §6.4: cap the LLM score at 60 for <15 words, 75 for <30 words. Apply this cap after the LLM returns, before combining with the deterministic score.

### 8.5 Band definitions

Per spec §6.3, include the band table in the prompt so the LLM has the same banded judgement framework as the other LLM metrics.

---

## 9. Wiring into `scoreSample()`

In `scorer-arabic.html` around line 3673, the function `scoreSample()` parallelises all LLM calls via `Promise.all` with `_maybeCall(_dimEnabled(id), ...)`.

### 9.1 Add the LLM call

Add to the `Promise.all` array:

```js
_maybeCall(_dimEnabled("orthographic_control"), orthoPrompt, null, "ORTHO", { max_tokens: 1024 })
```

Bind the result to `orthoData`.

### 9.2 Compute the deterministic branch

Outside the `Promise.all` (deterministic computation is synchronous), compute:

```js
const orthoDet = _dimEnabled("orthographic_control") && wc >= 10
  ? computeArabicOrthography(response, { allow_loanword_list: [], titles: ARABIC_TITLES, list_versions: { ... } })
  : null;
```

The `wc >= 10` gate enforces the 10-word floor. If false, the dimension contributes `null` (treated as N/A* by the existing pipeline).

### 9.3 Extract LLM score

```js
const orthoLLMScoreRaw = orthoData?.llm_orthographic_accuracy_score ?? orthoData?.score ?? null;
let orthoLLMScore = (typeof orthoLLMScoreRaw === "number") ? orthoLLMScoreRaw : null;
const orthoLLMJustification = orthoData?.justification ?? "";
// Apply short-response cap
if (orthoLLMScore !== null) {
  if (wc < 15) orthoLLMScore = Math.min(orthoLLMScore, 60);
  else if (wc < 30) orthoLLMScore = Math.min(orthoLLMScore, 75);
}
```

### 9.4 Combine into Orthographic Control score using calibration weights

Use the same `_metricPct` helper used by the other composite dimensions:

```js
let orthographicControlScore = null;
if (_dimEnabled("orthographic_control") && orthoDet && typeof orthoLLMScore === "number") {
  orthographicControlScore = Math.round(
    orthoDet.technical_quality        * _metricPct("orthographic_control", "technical_quality") +
    orthoDet.common_error_detection   * _metricPct("orthographic_control", "common_error_detection") +
    orthoLLMScore                     * _metricPct("orthographic_control", "llm_orthographic_accuracy")
  );
}
```

With default weights (24 / 36 / 40), this is mathematically equivalent to `Det × 0.60 + LLM × 0.40` from the spec.

### 9.5 Add to `_dimScoreMap`

In the Overall computation block (around line 3820):

```js
const _dimScoreMap = {
  task_achievement: taFinal,
  content_quality: cqFinal,
  style_register: styleRegisterScore,
  language_range: languageRangeScore,
  organisation_coherence: orgCohScore,
  language_accuracy: grammarScore,
  orthographic_control: orthographicControlScore   // ← new
};
```

The existing weighted-sum-over-enabled-valid-dimensions logic handles the rest automatically. N/A* (null) responses are already excluded from Overall.

### 9.6 Add to the return object

Add the OC fields to the object returned at the bottom of `scoreSample()`, including:

```js
orthographic_control: orthographicControlScore,
orthographic_control_breakdown: orthoDet ? {
  ...orthoDet,
  llm_orthographic_accuracy: orthoLLMScore,
  llm_justification: orthoLLMJustification,
  final_score: orthographicControlScore
} : null
```

This shape matches spec §8 output schema.

---

## 10. Results panel UI

In the Results tab (`view-step3` / view ID 3), add an Orthographic Control display block matching the style of the existing dimension cards. Required content:

1. Headline score `/100`.
2. Two sub-scores: Deterministic Orthography Score and LLM Orthographic Accuracy, each `/100`.
3. Expandable "Flags" list showing the entries from `flags` (incorrect → suggested, with tier badge and occurrences count).
4. LLM justification text.
5. List version strings (small grey footer text — for audit trace).

Match the existing dimension-card CSS (`.dim-card`, `.score-pill`, etc. — grep for the patterns used by Style & Register or Language Range, which also have composite sub-scores).

When the dimension returns `N/A*` (< 10 words), show "Not scored — response below 10-word floor" in place of the score, same way other short-response N/A* cases are handled.

---

## 11. Out of scope

Do NOT build in this step:

- Full Arabic spell-checking (V1.1 §12).
- Morphological parsing.
- Diacritic (harakat) evaluation.
- Named-entity recognition beyond the title-based proper-noun gate.
- Automatic correction generation (the flags list shows suggestions, but no auto-rewrite).
- Configurable density multipliers in the UI (spec §10 is a future enhancement).
- A separate "Orthography lists admin" UI. List edits happen by editing the JSON files + re-syncing the inlined constants.
- Diff between current and previous list versions.

---

## 12. Acceptance criteria

The build is done when:

1. `Final info/config/` exists and contains three JSON files with the seed contents from §5.
2. The three lists are also present as inlined JS constants in `scorer-arabic.html` with sync banners (per §5.4 Option A).
3. The Calibration tab now shows 7 dimensions. Defaults render with all weights at `100/7 ≈ 14.29 %`, summing to 100.00 %.
4. Expanding Orthographic Control reveals three siblings: Technical Quality 24.0, Common Error Detection 36.0, LLM Orthographic Accuracy 40.0, summing to 100.00 %.
5. Users with an existing 6-dimension config in localStorage (from Step 1) get auto-migrated to 7 dimensions on next page load, with their previous weights preserved and proportionally rescaled.
6. Running scoring on the worked example response from spec §9 produces these intermediate values (regression test):
   - Technical Quality = 100
   - Common Error Detection = 39
   - Deterministic Orthography Score = 63
   - Orthographic Control with default calibration = 58 (allowing LLM = 50; the LLM result will vary by run, so accept ±5)
7. The Results panel shows a new Orthographic Control card with score, sub-scores, flags list, and justification.
8. With Orthographic Control **disabled** in the calibration tab, no LLM call is made for it, no flags are shown, and the Overall is computed over the other enabled dimensions only — matching pre-Step-2 behaviour for those dimensions.
9. With the dimension enabled but the response under 10 words, the dimension returns N/A* and is excluded from Overall.
10. The proper-noun gate suppresses `علي` flagging when preceded by `السيد` / `الأستاذ` / `الدكتور` / `الشيخ` / `سيدي` or appearing inside quotes.

### Regression check (must pass)

Run scoring on a saved sample from before Step 2 with default calibration. The 6 existing dimension scores must be **identical** to their pre-Step-2 values. The Overall may change because it now includes a 7th dimension at 1/7 weight — that's expected. To verify the 6 existing scores are unchanged, look at each dimension column in the Results table.

### Worked-example regression (deterministic branch only)

Response (24 words):

> يجب علي كل شخص ان يحافظ على البيئة. مثلا انت يجب ان تحافظ على المدرسه و المكتبه. في حياه الناس يجب ان نزرع الاشجار.

Expected intermediate values from `computeArabicOrthography`:

- `technical_quality_breakdown` = { punctuation: 100, whitespace: 100, tatweel: 100, non_arabic_intrusion: 100 }
- `technical_quality` = 100
- `common_error_detection_breakdown` = { taa_marbuta: 0, alif_forms: 83, hamza: 33 }
- `common_error_detection` = 39 (mean of 0, 83, 33 → 38.67, rounded to 39)
- `deterministic_orthography_score` = 63 (100 × 0.40 + 39 × 0.60 = 63.4 → 63)
- `flags` includes the six entries from spec §9 table

Implementations that don't reproduce these exact intermediates have diverged from the spec — fix the implementation, not the spec.

---

## 13. Visual / quality bar

- Match the existing card/tab/typography patterns in `scorer-arabic.html`. No new design language.
- All CSS inline in the existing `<style>` block. No new files except the three JSONs in `Final info/config/`.
- All JS in the existing `<script>` block. No new modules.
- Comment the new code blocks with banner headers like the existing pattern:

```
// ============= ORTHOGRAPHIC CONTROL =============
// ...
// ============= END ORTHOGRAPHIC CONTROL =============
```

- LLM prompt lives in the prompts block with the others, identifier `"ORTHO"`.
- Curated-list constants live near the top of the script block, after `CALIB_DEFAULTS`, before the scoring functions.

---

## 14. Order of work (suggested)

1. Create `Final info/config/` and the three JSON files.
2. Inline the lists as JS constants with sync banners.
3. Write `computeArabicOrthography()` and verify against the spec §9 worked example in isolation (console.log driven).
4. Add `orthographic_control` to `CALIB_DEFAULTS`, update `_EW`, write the migration.
5. Verify the Calibration tab shows 7 dimensions correctly with auto-rebalance and migration from a 6-dim localStorage.
6. Add the LLM prompt and the `_maybeCall` in `scoreSample()`.
7. Wire `orthographicControlScore` into `_dimScoreMap` and the return object.
8. Add the Results panel display.
9. Run end-to-end on the spec's worked example. Confirm deterministic intermediates match exactly; accept LLM variation ±5.
10. Regression check: a pre-Step-2 sample's 6 existing dimensions are unchanged with default calibration.

When all 10 acceptance criteria pass, push and Vercel will deploy.
