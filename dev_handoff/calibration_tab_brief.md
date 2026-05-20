# Implementation Brief: Calibration Tab

**For:** Claude Code / Cursor
**Project:** scorer-arabic.html — Arabic writing scorer prototype
**Author:** Richard
**Date:** 2026-05-20
**Status:** Step 1 of a two-step build. Step 2 (Orthographic Control dimension) follows in a separate brief.

---

## 1. Context

This is a single-file browser app for scoring Arabic writing samples. It is built on the architecture of the English equivalent (`scorer.html`) and uses the same Vercel serverless function for OpenAI / Anthropic proxying.

### Project root

```
C:\Users\richa\Desktop\TASK ACHIEVEMENt and CONTENT QUALITY\
```

### Files to know about

| File | Role | Action |
|------|------|--------|
| `scorer-arabic.html` | The app you are editing. ~4,283 lines. HTML + CSS + JS in one file. | **Edit** |
| `scorer.html` | The English version — same architecture, smaller scope. | **Reference only — do not edit.** |
| `api/openai.js` | Vercel serverless function proxying to OpenAI / Anthropic. | **No changes needed.** |
| `Final info/scoring_overview.md` | High-level scoring methodology (English version doc). | Read for context. |
| `Final info/orthographic_control_spec_v1.1.md` | Spec for the new 7th dimension being added in Step 2. | Read for context; **do not implement in this step.** |
| `dev_handoff/` | This brief lives here. Other handoff notes also live here. | — |

### Existing tab structure (do not change order — only add)

The app currently has four tabs:

```
[ Scoring System ]  [ 1. Create Question ]  [ 2. Test Samples ]  [ 3. Results ]
        ↑
   view-step0           view-step1                 view-step2          view-step3
```

You will add a new tab **between "Scoring System" and "1. Create Question"**, called **"Calibration"** — view ID `view-calibration`.

### Existing scoring dimensions

The app currently scores six dimensions (search `<h3` in `scorer-arabic.html` from line ~580 for the canonical list and weighting math):

1. **Task Achievement** — composite of WCC (Word Count Compliance, code-based), TA (Task Requirements, LLM), IE (Intelligibility & Effect, LLM). Formula: `WCC × 0.40 + ((TA × 0.80) + (IE × 0.20)) × 0.60`. For calibration purposes, expose these as three sibling metrics with effective weights WCC 40, TA 48, IE 12.
2. **Content Quality** — single metric.
3. **Style & Register** — composite of MSA (70%) and Dialect (30%).
4. **Language Range** — composite of Vocab (33.4%), Morphology (33.3%), Sentence Complexity (33.3%).
5. **Organisation & Coherence** — composite of Cohesive Devices code-scan (30%) and Coherence & Flow LLM (70%).
6. **Language Accuracy** — single metric.

A 7th dimension (Orthographic Control) will be added in Step 2 — **not in this step**.

---

## 2. What to build

A new **Calibration** tab that lets the user:

- Enable / disable any dimension via a checkbox.
- Set the percentage weight of each enabled dimension (default: equal weighting across enabled dimensions).
- Expand a dimension (collapsible row) to view and tweak the weights of its inner metrics.
- See live totals at every level. Totals must always sum to 100 within an enabled scope; auto-rebalance handles this.
- Reset to defaults via a single button.

Calibration is saved to `localStorage` and used the **next time** Run Scoring is invoked. There is **no preview / live re-score** of past results.

---

## 3. UI layout

Follow the existing card / view / tab CSS patterns (`.card`, `.view`, `.tab`). Match the visual language already in the file. No new fonts, no new colour tokens beyond what's already in `:root`.

### Mock (logical structure)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Calibration                                                         │
│  Tune the weight each dimension carries in the Overall Score, and    │
│  the weight each metric carries within its dimension. Changes save   │
│  automatically and apply on the next Run Scoring.                    │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  ☑  Task Achievement              [ 16.67 ] %    [ ▸ ]      │    │
│  │  ☑  Content Quality                [ 16.67 ] %                │    │
│  │  ☑  Style & Register               [ 16.67 ] %    [ ▸ ]      │    │
│  │  ☑  Language Range                 [ 16.67 ] %    [ ▸ ]      │    │
│  │  ☑  Organisation & Coherence       [ 16.67 ] %    [ ▸ ]      │    │
│  │  ☑  Language Accuracy              [ 16.65 ] %                │    │
│  │                                              Total:  100.00 % │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  [ Reset to defaults ]                            Saved 2 sec ago    │
└─────────────────────────────────────────────────────────────────────┘
```

Expanded example (Task Achievement open):

```
│  ☑  Task Achievement                 [ 16.67 ] %    [ ▾ ]   │
│       ├── Word Count Compliance           [ 40.0 ] %        │
│       ├── Task Requirements (LLM)         [ 48.0 ] %        │
│       └── Intelligibility & Effect (LLM)  [ 12.0 ] %        │
│                                       Sub-total: 100.00 %   │
```

### Behaviour notes for the UI

- **Disabled dimensions** are visually dimmed and their weight field is greyed but still shows their last value (so re-enabling restores it sensibly).
- **Expand caret** only appears on dimensions that have inner metrics (Content Quality and Language Accuracy have none, so no caret).
- **Live total** at the bottom of the dimension list always sums to 100 across **enabled** dimensions. If any rounding leaves it at 99.99 or 100.01, show 100.00 — the underlying full-precision values are what's used.
- **Save indicator** in the corner (e.g. "Saved 2 sec ago") — small text, no toast.

---

## 4. Behaviour rules

### 4.1 Auto-rebalance

Whenever a dimension is enabled/disabled or any weight changes, redistribute proportionally so totals stay at 100. Pseudocode:

```js
function rebalance(scope, changedItemId, newWeight) {
  // scope = { dimensions } at top level, or { metrics } inside a dimension
  // newWeight is the new value of the changed item
  // Distribute (100 - newWeight) across the other enabled items, scaled by their current weights.
  // If a single item is enabled and the user sets it below 100, snap it to 100 (only option).
}
```

Disabling a dimension: its weight becomes 0 effectively, and its share is redistributed among the remaining enabled dimensions proportionally.

Re-enabling a dimension: it claims back a proportional share. Simplest implementation: when re-enabled, give it the average of currently-enabled dimensions' weights and rebalance the rest down.

### 4.2 Persistence

- Save to `localStorage` under key `azescorer.arabic.calibration` on every change, debounced ~300 ms.
- Load on app init. If absent or schema-mismatched, fall back to defaults (§6) and write them out.
- Save also writes `updated` ISO-8601 timestamp.

### 4.3 Scoping

- This is a single configuration. **No multiple named calibrations.** No load/save buttons. No import/export.
- Weights only — **do not** expose formula constants (multipliers, density bands, error-rate factors).

### 4.4 Reset to defaults

A button that returns the entire configuration to the defaults in §6 and re-saves.

---

## 5. Data shape

Stored in `localStorage` as JSON under key `azescorer.arabic.calibration`. Schema:

```json
{
  "version": "1.0",
  "updated": "2026-05-20T14:23:00Z",
  "dimensions": [
    {
      "id": "task_achievement",
      "label": "Task Achievement",
      "enabled": true,
      "weight_pct": 16.67,
      "metrics": [
        { "id": "wcc", "label": "Word Count Compliance",   "weight_pct": 40.0 },
        { "id": "ta",  "label": "Task Requirements (LLM)", "weight_pct": 48.0 },
        { "id": "ie",  "label": "Intelligibility & Effect","weight_pct": 12.0 }
      ]
    },
    {
      "id": "content_quality",
      "label": "Content Quality",
      "enabled": true,
      "weight_pct": 16.67,
      "metrics": []
    },
    {
      "id": "style_register",
      "label": "Style & Register",
      "enabled": true,
      "weight_pct": 16.67,
      "metrics": [
        { "id": "msa",     "label": "MSA Consistency",    "weight_pct": 70.0 },
        { "id": "dialect", "label": "Dialect Detection",  "weight_pct": 30.0 }
      ]
    },
    {
      "id": "language_range",
      "label": "Language Range",
      "enabled": true,
      "weight_pct": 16.67,
      "metrics": [
        { "id": "vocab",    "label": "Vocabulary Diversity",  "weight_pct": 33.4 },
        { "id": "morph",    "label": "Morphological Variety", "weight_pct": 33.3 },
        { "id": "sentence", "label": "Sentence Complexity",   "weight_pct": 33.3 }
      ]
    },
    {
      "id": "organisation_coherence",
      "label": "Organisation & Coherence",
      "enabled": true,
      "weight_pct": 16.67,
      "metrics": [
        { "id": "cohesive_devices", "label": "Cohesive Devices (code)", "weight_pct": 30.0 },
        { "id": "coherence_flow",   "label": "Coherence & Flow (LLM)",  "weight_pct": 70.0 }
      ]
    },
    {
      "id": "language_accuracy",
      "label": "Language Accuracy",
      "enabled": true,
      "weight_pct": 16.65,
      "metrics": []
    }
  ]
}
```

Notes:

- Store full-precision values internally; display rounded to 1 dp. Rounding deltas absorb into the last dimension's `weight_pct` so the sum is exactly 100.00 on save.
- `id` fields are stable strings — used to match against the scoring pipeline's existing names. Do not change these without grepping the file.

---

## 6. Defaults

These are the values returned by "Reset to defaults" and used when no `localStorage` exists.

| Dimension | Enabled | Weight % | Inner metric defaults |
|-----------|---------|----------|-----------------------|
| Task Achievement | true | 16.67 | WCC 40, TA 48, IE 12 |
| Content Quality | true | 16.67 | — |
| Style & Register | true | 16.67 | MSA 70, Dialect 30 |
| Language Range | true | 16.67 | Vocab 33.4, Morph 33.3, Sentence 33.3 |
| Organisation & Coherence | true | 16.67 | Cohesive Devices 30, Coherence & Flow 70 |
| Language Accuracy | true | 16.65 | — |

The dimension defaults match the *current* hard-coded weighting behaviour of the app, so "default calibration" produces identical scores to the pre-calibration version.

---

## 7. Wiring into scoring

The current scoring pipeline (search `Overall = mean(...)` and the per-dimension combine functions in `scorer-arabic.html`) uses hard-coded weights. Replace those with reads from the active calibration config.

### Rules

1. **Disabled dimensions are not scored at all.** Skip their LLM calls and code paths. Do not include them in the results table.
2. **Overall Score** = weighted sum of enabled-dimension scores divided by 100. With all enabled and at defaults, this should equal the existing equal-weight mean.
3. **Inner metric weights** replace the hard-coded composite formulas. E.g. Style & Register becomes `MSA × (msa_pct/100) + Dialect × (dialect_pct/100)`.
4. **Task Achievement** is flattened for calibration. Replace the existing nested formula `WCC × 0.40 + ((TA × 0.80) + (IE × 0.20)) × 0.60` with `WCC × (wcc_pct/100) + TA × (ta_pct/100) + IE × (ie_pct/100)`. Defaults (40/48/12) reproduce the current formula exactly.
5. **N/A* handling** is unchanged. If a metric returns N/A* (short-response floor), it is excluded from its dimension's average and weights of the remaining metrics are re-normalised proportionally just for that response.

### Where the calibration config is read

Expose a single global accessor, e.g. `getCalibration()`, that returns the parsed config from localStorage (or the defaults if absent). The scoring functions call this once per scoring run.

---

## 8. Out of scope (do NOT build in this step)

- The Orthographic Control dimension itself. The calibration tab ships with 6 dimensions only. OC arrives in Step 2 and will add itself to the calibration tab at that point.
- Multiple saved calibrations.
- Import / export of calibrations.
- Exposing formula constants (multipliers, thresholds, density bands).
- Live re-scoring of past results in the Results tab when calibration changes.
- Server-side persistence (this is localStorage only).
- Validation rules beyond rebalancing (e.g. no minimum weight, no maximum, no warnings for "unusual" configs).

---

## 9. Acceptance criteria

The build is done when:

1. A "Calibration" tab appears between "Scoring System" and "1. Create Question".
2. Default state shows 6 dimensions, all enabled, weights summing to exactly 100.00 %.
3. Toggling a checkbox or editing a weight auto-rebalances and persists to localStorage within ~300 ms.
4. Expanding a dimension reveals its metrics with their own editable weights, also auto-rebalanced.
5. Reloading the browser restores the saved calibration.
6. Running scoring with default calibration produces identical results to the pre-change version (regression check).
7. Running scoring with one dimension disabled excludes that dimension from the results table and recomputes Overall over the remaining ones.
8. Running scoring with non-default weights produces an Overall that matches a manual weighted sum of the dimension scores.
9. "Reset to defaults" returns the UI and localStorage to §6 values.

---

## 10. Visual / quality bar

- Match the existing card/tab/typography patterns in `scorer-arabic.html`. Do not introduce a new design language.
- Keep all CSS inline in the `<style>` block at the top of the file. No new files.
- Keep all JS in the existing `<script>` block. No new modules, no new bundlers.
- Comment the calibration code block with a header banner the same way the file already uses (`// ============= CALIBRATION =============`).
