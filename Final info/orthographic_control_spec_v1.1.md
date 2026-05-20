# Product Specification

# Arabic Writing Assessment — Orthographic Control Dimension

**Version 1.1**

---

## 1. Overview

The Orthographic Control dimension evaluates a learner's ability to produce technically accurate written Arabic, focusing on spelling conventions, script accuracy, and orthographic correctness.

This dimension is intentionally separated from broader Language Accuracy scoring because Arabic orthography is a partially independent construct. A learner may demonstrate acceptable grammatical control while still producing recurring orthographic errors such as hamza misuse, taa marbuta confusion, or incorrect alif forms.

The dimension combines deterministic code-based analysis with scope-locked AI judgement. Every node in the scoring tree returns a value on a 0–100 scale, consistent with the rest of the scorer-arabic system.

---

## 2. Design Goals

- Measure Arabic-specific writing control as a distinct construct
- Improve scoring transparency and consistency
- Reduce reliance on fully holistic AI scoring
- Leverage deterministic code where reliability is high
- Restrict AI judgement to context-dependent orthographic questions only
- Support scalable, explainable, defensible Arabic writing assessment

---

## 3. Scoring Architecture

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

**Top-level formula**

```
Orthographic Control = Deterministic Orthography Score × 0.60
                     + LLM Orthographic Accuracy       × 0.40
```

**Deterministic branch**

```
Deterministic Orthography Score = Technical Quality       × 0.40
                                + Common Error Detection × 0.60
```

**Within Technical Quality**: equal-weight mean of the four sub-metrics.
**Within Common Error Detection**: equal-weight mean of the three sub-metrics.

Every node in the tree is 0–100. All averages are arithmetic means of 0–100 inputs, producing a 0–100 output.

---

## 4. Dimension Scope

**This dimension evaluates:** Arabic spelling control, hamza usage, taa marbuta correctness, alif form correctness, script consistency, and technical cleanliness of the writing.

**This dimension does NOT evaluate:** grammar, syntax, vocabulary, task achievement, coherence, register, or content quality. Those constructs are scored by other dimensions and must not influence the Orthographic Control score.

---

## 5. Deterministic Orthography Score

The deterministic branch evaluates orthographic features measurable by code with low false-positive risk. The system does not attempt full Arabic spell-checking — it is limited to high-confidence checks against either Unicode-level rules or curated lexical lists.

### 5.1 Technical Quality

Measures technical cleanliness and script professionalism.

#### 5.1.1 Arabic Punctuation Usage

Counts occurrences of Arabic punctuation: `،` `.` `؟` `:` `؛` `!`

Western-script punctuation used in place of Arabic equivalents is detected as a substitution error: `,` instead of `،`, `?` instead of `؟`, `;` instead of `؛`. (Full stop `.` and exclamation `!` are shared between scripts and not flagged as substitutions.)

**Scoring formula**

```
density = (arabic_punct_count / words) × 100
substitution_penalty = min(40, western_substitutions × 5)

score = base − substitution_penalty

where base =
  100                              if 5 ≤ density ≤ 20
  linear ramp 50 → 100              if 0 ≤ density < 5
  linear ramp 100 → 50              if 20 < density ≤ 40
  30                                if density > 40
```

#### 5.1.2 Whitespace & Formatting Quality

Detects: double spaces, missing space after punctuation, leading/trailing whitespace, more than two consecutive line breaks.

**Scoring formula**

```
score = max(0, 100 − 5 × issue_count)
```

Each formatting issue costs 5 points. No per-instance cap below the 0 floor.

#### 5.1.3 Tatweel Abuse

Detects decorative tatweel/kashida usage (`ـ`).

**Scoring formula**

```
score = 100                       if tatweel_count = 0
      = 70                        if tatweel_count = 1   (treated as typo)
      = max(0, 70 − 10 × (n − 1)) if tatweel_count > 1
```

Tatweel should not appear in typed assessment writing. A single occurrence is treated as a likely typing accident; repeated use is penalised steeply.

#### 5.1.4 Non-Arabic Character Intrusion

Detects Latin letters, emoji, digits in scripts other than the configured default, and non-Arabic punctuation beyond the substitution cases handled in §5.1.1.

Tokens listed in the optional `allow_loanword_list` (e.g. brand names, scientific terms, MoE-specified exceptions) pass without flagging. Default list is empty.

**Scoring formula**

```
intrusion_rate = (non_arabic_tokens / total_tokens) × 100
score = max(0, 100 − intrusion_rate × 8)
```

`intrusion_rate` of 0 returns 100. An intrusion rate of 12.5 % drives the sub-score to zero.

#### 5.1.5 Technical Quality Composite

```
Technical Quality = mean(Punctuation, Whitespace, Tatweel, Non-Arabic)
```

### 5.2 Common Error Detection

Detects high-frequency Arabic orthographic errors using curated lexical comparison lists. Each sub-metric returns 0–100 using the same density-based formula.

#### 5.2.1 Taa Marbuta (ة / ه) Confusion

Detects misuse of word-final ه where ة is expected.

| Incorrect | Correct |
|-----------|---------|
| مدرسه     | مدرسة   |
| حياه      | حياة    |
| شجره      | شجرة    |
| فكره      | فكرة    |
| مكتبه     | مكتبة   |

#### 5.2.2 Alif Form Confusion

Detects common confusion involving `ا`, `ى`, `أ`, `إ`.

| Incorrect | Correct |
|-----------|---------|
| الى       | إلى     |
| حتي       | حتى     |
| علي       | على     |
| موسي      | موسى    |

#### 5.2.3 Common Hamza Errors

Detects high-frequency hamza omissions or substitutions.

| Incorrect | Correct |
|-----------|---------|
| انت       | أنت     |
| اخذ       | أخذ     |
| مسئلة     | مسألة   |
| اولاد     | أولاد   |
| الاشجار   | الأشجار |

#### 5.2.4 Scoring Formula (shared)

Each Common Error Detection sub-metric uses:

```
unique_errors = count of distinct flagged forms after dedup
error_rate    = (unique_errors / words) × 100
score         = max(0, 100 − error_rate × 8)
```

**Calibration target:** 0 errors per 100 words → 100; ~3 errors per 100 words → ~76 ("Acceptable"); ~12.5 errors per 100 words → 0 ("Severe"). The multiplier `8` is a calibration parameter and may be tuned per category once marker-agreement data is available.

#### 5.2.5 Dedup Rule

If the same misspelled form occurs multiple times, it is counted as **one unique error** for scoring purposes. All occurrences are still recorded in the output `flags` array for the teacher report. This protects scoring from being dominated by one repeated mistake while preserving full visibility for feedback.

#### 5.2.6 Common Error Detection Composite

```
Common Error Detection = mean(Taa Marbuta, Alif, Hamza)
```

### 5.3 False-Positive Policy

Curated-list flagging needs to handle cases where the "incorrect" form is legitimately correct in context.

**Confidence tiers.** Each curated-list entry is tagged with a confidence level:

| Tier | Meaning | Effect |
|------|---------|--------|
| `always_wrong` | The form is never correct in MSA writing (e.g. `مدرسه` for `مدرسة`). | Full-weight penalty. |
| `usually_wrong` | The form is usually an error but has legitimate uses (e.g. `علي` is a male name as well as a misspelling of `على`). | Half-weight penalty (counted as 0.5 unique errors). |

**Proper-noun gate.** A `usually_wrong` candidate is **not** flagged when it is preceded by a recognised title (`السيد`، `الأستاذ`، `الدكتور`، `الشيخ`، `سيدي`) or appears between quotation marks. This handles personal-name false positives without requiring a full named-entity recogniser.

**Calibration pruning.** During the calibration phase (§10), per-entry false-positive rate is tracked. Entries with FP rate above 15 % are demoted from `always_wrong` to `usually_wrong`, or removed from the list. List versions are tagged in the output schema.

### 5.4 Curated List Governance

Curated lists are JSON files held in `Final info/config/`:

- `orthography_taa_marbuta.json`
- `orthography_alif.json`
- `orthography_hamza.json`

Each entry has the form:

```json
{
  "incorrect": "مدرسه",
  "correct":   "مدرسة",
  "tier":      "always_wrong",
  "added":     "2026-05-21",
  "added_by":  "richard"
}
```

Lists are versioned with a semver string (`v1.0.0`) and the version is recorded in each score's output so a score can always be reproduced against the list state at the time of scoring. Additions to the list require a single false-positive review on a 100-essay sample before merging.

---

## 6. LLM Orthographic Accuracy

Evaluates orthographic correctness that cannot be measured reliably through deterministic code: in-context hamza placement on hamza-bearers, taa marbuta in non-listed words, general spelling beyond curated patterns, and overall orthographic consistency.

### 6.1 Scope Restrictions

The LLM evaluates **only**: hamza correctness, general spelling accuracy, taa marbuta correctness, alif forms, orthographic consistency.

The LLM **must not** evaluate: grammar, vocabulary range, coherence, content quality, register, task achievement.

### 6.2 Letter-Form Distribution Context

To help the LLM detect anomalies, the deterministic layer provides letter-form counts as context to the LLM prompt:

```
{ "alif": 42, "alif_hamza_above": 8, "alif_hamza_below": 3, "alif_madda": 0,
  "alif_maqsura": 5, "taa_marbuta": 11, "haa_final": 2, "hamza_isolated": 1,
  "hamza_yaa": 4, "hamza_waw": 2, "words": 120 }
```

This is a descriptive feature — it does not directly score anything but lets the LLM flag suspicious distributions (e.g. zero `ة` in 200 words of expository writing).

### 6.3 Band Definitions

| Band | Score | Interpretation |
|------|-------|----------------|
| Strong | 81–100 | Strong orthographic control with minimal errors |
| Generally accurate | 61–80 | Accurate with noticeable recurring issues |
| Unstable | 41–60 | Frequent orthographic instability |
| Persistent problems | 21–40 | Persistent spelling and script control problems |
| Severe | 0–20 | Severe orthographic breakdown |

### 6.4 Band Pressure Rules

**81+ entry requirements.** A score above 80 requires consistent hamza accuracy across both initial and medial positions, minimal taa marbuta errors (0–1 per 100 words), strong spelling stability, and no recurring script inconsistency.

**Short-response caps.** Aligned with the global short-response caps used elsewhere in scorer-arabic:

| Word count | Maximum LLM score |
|------------|-------------------|
| < 15 words | 60 |
| < 30 words | 75 |

### 6.5 Anti-Leakage Prompt Design

The LLM prompt includes explicit examples to prevent grammar / vocabulary / coherence leakage into the orthographic score. Examples in the prompt include:

- *"A response with bad verb conjugation but perfect hamza placement should score high on this metric."*
- *"A response that goes off-topic but spells everything correctly should score high on this metric."*
- *"A response written in dialect but with consistent orthographic conventions should score high on this metric. Dialect detection belongs to Style & Register, not here."*

The prompt runs at `temperature: 0` consistent with the rest of the system.

---

## 7. Minimum Length Threshold

Below **10 words**, the dimension returns `N/A*`. This is lower than the system-wide 30-word floor because orthography can be meaningfully assessed on very short responses, where most other dimensions cannot.

When the dimension returns `N/A*`, it is excluded from the Overall Score calculation (the equal-weight average is taken over the remaining valid dimensions).

---

## 8. Output Schema

```json
{
  "orthographic_control": {
    "final_score": 56,
    "deterministic_orthography_score": 60,
    "technical_quality": 100,
    "technical_quality_breakdown": {
      "punctuation": 100,
      "whitespace": 100,
      "tatweel": 100,
      "non_arabic_intrusion": 100
    },
    "common_error_detection": 33,
    "common_error_detection_breakdown": {
      "taa_marbuta": 0,
      "alif_forms": 67,
      "hamza": 33
    },
    "llm_orthographic_accuracy": 50,
    "flags": [
      { "type": "taa_marbuta", "text": "مدرسه",  "suggested": "مدرسة",  "tier": "always_wrong",  "occurrences": 1 },
      { "type": "taa_marbuta", "text": "مكتبه",  "suggested": "مكتبة",  "tier": "always_wrong",  "occurrences": 1 },
      { "type": "taa_marbuta", "text": "حياه",   "suggested": "حياة",   "tier": "always_wrong",  "occurrences": 1 },
      { "type": "alif",        "text": "علي",    "suggested": "على",    "tier": "usually_wrong", "occurrences": 1 },
      { "type": "hamza",       "text": "ان",     "suggested": "أن",     "tier": "always_wrong",  "occurrences": 3 },
      { "type": "hamza",       "text": "انت",    "suggested": "أنت",    "tier": "always_wrong",  "occurrences": 1 }
    ],
    "flags_summary": {
      "taa_marbuta": { "unique": 3, "occurrences": 3 },
      "alif":        { "unique": 1, "occurrences": 1 },
      "hamza":       { "unique": 2, "occurrences": 4 }
    },
    "list_versions": {
      "taa_marbuta": "v1.0.0",
      "alif":        "v1.0.0",
      "hamza":       "v1.0.0"
    },
    "llm_justification": "Generally readable; recurring hamza omissions on common particles (أن, أنت) and several taa marbuta errors reduce orthographic accuracy. Alif maqsura confusion on على is a single instance and likely careless."
  }
}
```

---

## 9. Worked Example

**Response (24 words):**

> يجب علي كل شخص ان يحافظ على البيئة. مثلا انت يجب ان تحافظ على المدرسه و المكتبه. في حياه الناس يجب ان نزرع الاشجار.

**Identified flags after curated-list matching:**

| Type | Form | Suggested | Tier | Occurrences |
|------|------|-----------|------|-------------|
| taa_marbuta | مدرسه | مدرسة | always_wrong | 1 |
| taa_marbuta | مكتبه | مكتبة | always_wrong | 1 |
| taa_marbuta | حياه | حياة | always_wrong | 1 |
| alif | علي | على | usually_wrong | 1 |
| hamza | ان | أن | always_wrong | 3 |
| hamza | انت | أنت | always_wrong | 1 |

(`الاشجار` would be flagged if it were in the curated hamza list; assume here it is not, and is left to the LLM.)

**Technical Quality**

- Punctuation density = 2 / 24 × 100 = 8.3 → in range → **100**
- Whitespace issues = 0 → **100**
- Tatweel count = 0 → **100**
- Non-Arabic intrusion rate = 0 → **100**
- Technical Quality = mean(100, 100, 100, 100) = **100**

**Common Error Detection** (after dedup, `usually_wrong` counts as 0.5)

- Taa marbuta unique errors = 3 → density = 12.5 → score = max(0, 100 − 12.5 × 8) = **0**
- Alif unique errors = 0.5 (one `usually_wrong`) → density = 2.08 → score = max(0, 100 − 16.7) = **83**
- Hamza unique errors = 2 → density = 8.33 → score = max(0, 100 − 66.7) = **33**
- Common Error Detection = mean(0, 83, 33) = **39**

**Deterministic Orthography Score** = 100 × 0.40 + 39 × 0.60 = 40 + 23.4 = **63**

**LLM Orthographic Accuracy** (banded judgement, short-response cap applied at <30 words = 75):
LLM judges the response as "frequent orthographic instability" (band 41–60). Returns **50**.

**Orthographic Control** = 63 × 0.60 + 50 × 0.40 = 37.8 + 20 = **58**

This worked example serves as a regression test: any implementation that does not produce these intermediate values from this input has diverged from the spec.

---

## 10. Calibration Plan

Before bid submission (or as soon after as expert-marker samples are available), the dimension is calibrated against a panel of expert MoE markers.

**Sample size:** minimum 100 responses spanning the full proficiency range, with three independent expert orthography ratings per response.

**Metrics reported:**

- Exact-match agreement between AI score and human consensus band (target ≥ 65 %).
- Within-1-band agreement (target ≥ 85 %).
- Cohen's kappa (target ≥ 0.6).
- Per-category false-positive rate on the curated lists (target < 15 %).

**Calibration tuning levers** (in priority order):

1. Per-category multipliers in §5.2.4 (default 8, may diverge per category).
2. Confidence-tier reassignments based on observed FP rates.
3. List entry pruning for entries with FP rate > 15 % that cannot be saved by tier reassignment.
4. LLM prompt revisions, particularly to the anti-leakage examples in §6.5.
5. Weight adjustments at the top-level (Deterministic vs LLM, default 0.60 / 0.40) only as a last resort.

---

## 11. Design Principles

**Deterministic first.** Code is used wherever it is reliable.

**Scope-locked AI.** LLM judgement is restricted to a single, clearly defined construct.

**Explainability.** Every penalty is traceable to either a deterministic rule or a specific LLM reasoning statement.

**Arabic-specific validity.** The dimension reflects the genuine demands of Arabic writing — hamza, taa marbuta, alif forms, diglossic register — not a translated ESL framework.

**Auditable scoring math.** Every node in the scoring tree is 0–100, every weighted average is documented, and every score can be reproduced from inputs plus the recorded list versions.

---

## 12. V1 Limitations

V1.1 does NOT attempt:

- Full Arabic spellchecking
- Morphological parsing
- Dialect-aware spelling normalisation
- Context-sensitive hamza rule engines
- Automatic correction generation
- Diacritics (harakat) evaluation
- Named-entity recognition beyond the title-based proper-noun gate (§5.3)

---

## 13. V2 Possibilities

- Morphological analysis (Farasa / MADAMIRA integration)
- Root-pattern consistency checking
- Diacritic-sensitive scoring for advanced levels
- Native lexicon expansion via Hunspell-Arabic or AraComLex
- Context-aware hamza rules
- Dialect-aware tolerance models
- Per-category severity weighting tuned by calibration
- Orthographic fluency / typing-rhythm metrics where input timing data is available

---

## 14. Change Log

**V1.1 (2026-05-20)**

- Renamed top-level branches: "Code Score" → Deterministic Orthography Score; "Technical Writing Quality" → Technical Quality.
- Added explicit 0–100 scoring formulas for every code sub-metric.
- Added false-positive policy with `always_wrong` / `usually_wrong` confidence tiers.
- Added proper-noun gate for personal-name false positives.
- Added dedup rule and error-density normalisation.
- Added 10-word minimum length threshold.
- Added letter-form distribution as an LLM prompt context feature.
- Added curated list governance (file locations, versioning, addition workflow).
- Added anti-leakage prompt design with explicit examples.
- Added calibration plan with target agreement metrics.
- Added a fully worked example for regression testing.
- Updated output schema: `flags_summary`, `list_versions`, renamed `llm_reasoning` → `llm_justification`.
- Tightened §5.1.1 punctuation check to detect specific Western-script substitutions.
- Tightened §5.1.3 tatweel rule to treat a single tatweel as a likely typo.
- Tightened §5.1.4 with `allow_loanword_list` config.
