# Audit: AI rebuild (AZE console) vs scorer-arabic-v2.html + HANDOVER DOCS

**Date:** 2026-06-10
**Compared:** the pasted "AZE · Arabic Writing Scorer — Pipeline Console" HTML vs `scorer-arabic-v2.html` and the specs in `HANDOVER DOCS/`.

## Verdict in one paragraph

The scoring arithmetic is a faithful port — weights, formulas, caps, null handling, the verifier, and the halt rules all match the handover spec (and in four places the rebuild follows the spec where v2 had drifted). The prompts are *mostly* the same but **all the Arabic calibration examples were stripped out**, the **per-question development markers are no longer used**, and there are **three real scoring bugs/divergences** in the deterministic orthography maths and the construct-attempt counting. The rebuild is also a much slimmer app — the question tools, batch runner, feedback tabs, and most of the calibration suite are gone.

---

## 1. Prompts — same skeleton, missing calibration content

The wording, bands, caps, JSON output shapes, and the shared ANNOTATION DISCIPLINE block match v2/spec almost verbatim. What changed:

### Missing from the rebuild (was in v2 and the spec)

| Prompt | What's missing | Why it matters |
|---|---|---|
| Task coverage | `<calibration:examples>` — 6 Arabic PASS/FAIL anchor sentences | These anchor what "specific detail" means; without them PASS/FAIL judgements will drift |
| Intelligibility & effect | `<calibration:arabic_bands>` (Arabic exemplars anchored at 52 / 68 / 83 / 78) **and** `<rule:observability>` | The band anchors are your main consistency tool for this dimension; observability is the "no inferred vividness" rule |
| Register | The "Examples worth surfacing" block (lexical/particle/contraction examples per dialect) | Detection guidance for heavy-dialect responses; the seven-family coverage list survived |
| Coherence & flow | `<anti_inference_examples>` (don't infer castles/museums/weather…) and the `<focus_on>` bullets | Anti-inference was added after real failures on travel narratives |
| Orthography (LLM) | Small cuts: the إن شاء الله example, the "wrong word written correctly" clarifier | Minor |
| Vocabulary | Dialect example list under CONSTRUCT PURITY (rule itself kept) | Minor |

### Content Quality — functional regression

The CQ prompt text is identical, **but the rebuild always passes a hard-coded generic 0–3 ladder as the development markers**. v2 formatted the real per-question markers (`TaskObject.development_markers`, your `dev_handoff/question_markers.json` work) into the prompt. The rebuild's task object hardcodes `development_markers: []`, so per-question marker anchoring is dead.

### Where the rebuild is MORE spec-faithful than v2

- **Accuracy prompt** now carries the ANNOTATION DISCIPLINE block and the two Arabic anchors from your 2026-05-21 brief (non-human plural agreement, dual المثنى endings). v2 had neither.
- **prompt_version echo** added to every prompt (spec asks for versioned prompts).
- Discipline block now included in AFC, orthography, coherence, and range prompts (spec 01f says it applies to all annotators; v2 omitted it from several).
- Two dropped annotators that were vestigial anyway: `task_meta` genre-fit (scores into nothing — DIV-014) — though its guardrail flag goes too, see §3.

### Numbers all match

All bands, hard caps and thresholds in the prompts are identical: vocab caps 20/25/30(40)/35/35, morphology 20/25/30/35, sentence complexity 15/35/25/30/50, coherence ceiling blockers 45/60/55, intelligibility caps 5/25/44 and gates 76/91, orthography bands and the 86/87+ evidence gate, CQ evidence-density rules (7-word and 12/15-word fragments).

---

## 2. Scoring logic — core engine matches; three divergences

### Confirmed identical to spec (and v2)

- Dimension weights 14.29×6 + 14.26; weighted average; **null-penalty only for Language Accuracy** (0 in numerator, weight kept); UNMEASURABLE dimensions excluded (N/A).
- Task Achievement: WCC tolerance bands (100→85→0), weighted pass-rate (1.0/1.0/0.5), 20/50/30 mix, IE-missing renormalisation (20/70, 50/70) with LOW confidence — no silent 50.
- CQ enforcement: no-evidence force-zero, density caps 3→2 and 2→1, mean×100/3, original scores preserved.
- Style & Register: 5 density bands, within-band position, +5 MSA bonus, −5 lapse penalty, ±2 consistency, ±3 overflow, 92 lapse cap, 65 no-MSA-evidence ceiling, ±0.005 borderline flag.
- Language Range: mean of three (0.334/0.333/0.333), dialect-dominant soft cap 60, all-null + attempt<20 → floor 30 (DIV-023), never substitute 50.
- Organisation & Coherence: devices 0.30 + flow 0.70, missing sub-score → 50, connective engine formula (category spread 60% + diversity 40%, و excluded, longest-first, clitic prefixes).
- Language Accuracy: validity gates (<25 attempt or ≥0.20 dialect → null, DIV-001), HIGH formula 100−min(60, density×4) with pfe caps 80/90, AFC ≥2-of-3 gate at 88, volume discount (max 20), MEDIUM ceiling 75, severity weights 1.0/1.2/0.7/1.0/1.5/0.8.
- Orthographic Control: 0.25/0.35/0.40 blend, advanced-evidence detector (≥3 distinct forms AND density ≥3/100 words), double cap at 83 (DIV-031).
- Verifier: all four passes incl. construct-leakage suppression, first-emitted-wins dedup, rejection priority, CQ two-tier normalisation with the exact إأآ→ا map.
- Pipeline halt on the four required families with no fake score (DIV-002 / DIV-022).
- **CEFR bands: the rebuild uses the spec bands (with plus-bands, C2 at 86+). v2 used older bands (no plus-bands, C2 at 85+, B2 at 63+). So CEFR labels will visibly differ from v2 — the rebuild is the correct one per spec.**
- Embedded word lists (dialect markers, connectives, orthographic lists, task-type requirements, CEFR JSON) are exact copies of the machine-readable spec data.

### Divergence 1 — Orthography CED loses the dedup rule (real bug)

Spec §5.2.6 and v2: the same misspelled form counts **once** per category, however often it appears. The rebuild counts **every occurrence**. A student writing الى five times is penalised 5× instead of 1× — Orthographic Control comes out lower than v2/spec for any repeated misspelling.

### Divergence 2 — Technical Quality is a crude approximation (real divergence)

Spec §5.1/v2: punctuation density ramps, capped substitution penalty, tatweel anchored at 70, token-level intrusion with a loanword allowlist, digits/emoji handling. The rebuild: binary punctuation 100/50, uncapped −10 per western mark, −15 per tatweel, −5 **per Latin character**, no allowlist. TQ is 25% of Orthographic Control, so this shifts scores.

### Divergence 3 — construct_attempt_score is computed from different inputs

This number gates whether Language Accuracy is scored at all, so it matters:

- **MSA past-tense count:** v2 used a تُ-with-damma regex (documented undercount); the rebuild uses a 25-verb wordlist + تُ. Counts will be much higher in the rebuild → more responses route to HIGH validity, smaller volume discounts. Arguably better, but it changes calibration vs every batch you ran on v2.
- **formal_lexis_count:** spec/v2 count `range:vocabulary` evidence annotations; the rebuild dropped that annotator and substitutes the vocab scorer's `grounded_in` length. Different basis.
- **Subordinator counting:** v2 did substring matching (overcounts أن inside أنا/لأن); the rebuild matches whole tokens. Stricter/better, but again different counts.

Net effect: LA validity routing and the volume discount will not reproduce v2's batch results.

### Smaller differences

- TA pass counting: v2 deduped by requirement_id (after finding source-matching fragile); the rebuild went back to source-based weight summing (capped at total, so bounded).
- Guardrail thresholds: EXTREME_LOW ≤10 (v2: ≤20), DIMENSION_SPREAD >50 (v2: ≥60); hardcoded in the rebuild, configurable in v2.
- `dialect_dominant_high_accuracy` trigger: profile-based + LA≥70 (v2: SR≤40 + LA≥75). `style_range_register_split`: |SR−LR|>50 (v2: LR>70 while MSA-consistency<50). `high_grammar_low_orthography` is now bidirectional — that one actually matches the spec better than v2.

---

## 3. Dropped annotators and evidence trail

These don't change scores directly (except via formal_lexis_count above) but remove spec-required evidence:

- `cohesion:device` per-match annotations (spec 06c says emit one per connective hit — only the snapshot survives)
- `cohesion:llm_observation` (teacher-facing diagnostic)
- `range:*_evidence` (5 subtypes) and `range:lexical_density`
- `task_meta:genre_fit` annotator + the `task_type_prompt_mismatch` guardrail flag
- `cq_evidence_reuse` guardrail contradiction (the confidence demotion survives, the teacher-visible flag doesn't)

---

## 4. Operational / feature changes

- **API client:** the rebuild calls `api.anthropic.com` directly from the browser with hardcoded `claude-sonnet-4`, no key, **max_tokens 1000**. v2 went through your `/api/openai` & `/api/claude` proxies with a model picker (GPT-5 etc.), max_tokens 2000, and throttling. The rebuild's live mode will not work on the Vercel deployment as-is, and 1000 tokens risks truncating the register annotator on heavy-dialect responses (there is a JSON-repair salvage, but truncated findings are lost).
- **Gone from v2:** question authoring (generate question/requirements/markers), batch runner, feedback & next-steps, FAQ/technical-guide tabs, sub-metric weight calibration, guardrail config, dialect-treatment setting, GSE mapping.
- **New in the rebuild:** offline deterministic demo mode, failure drill (DIV-002 test), prompt editor tab, all-annotations inspector with filters.

---

## 5. Recommended fixes, in order

1. Restore the **calibration example blocks** in the task-coverage, intelligibility, register, and coherence prompts (copy from `02e/03e/06e-prompts.md` — pure paste, no logic change).
2. Re-wire **development_markers** into the task object and CQ prompt (v2's formatting code is at line ~4651 of scorer-arabic-v2.html).
3. Fix **CED dedup** (count unique misspelled forms, not occurrences) and port the spec §5.1 **Technical Quality** components.
4. Decide deliberately on the **construct_attempt_score** inputs (past-tense wordlist vs regex; restore the range-evidence annotator or bless the grounded_in proxy) — then re-run a variance batch, because LA routing changed.
5. Point the live client back at your **/api proxies** and raise max_tokens to 2000.
