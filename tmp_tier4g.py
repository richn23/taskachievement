"""
Tier 4G - Orthographic Control refresh (04-dimension-orthographic-control.md)
Changes:
  A. Insert V1 curated lists + hasAdvancedOrthographicEvidence + computeArabicOrthography
     before annotateOrthographyCode (read from scorer-arabic.html verbatim)
  B. Rewrite annotateOrthographyCode to use curated lists + sentinel annotation
  C. Extend annotateOrthographyLLM with bands + grounded_in + absence-is-not-mastery
  D. Update POLARITY_REGISTRY: add deterministic_snapshot + ceiling_score; retire common_error
  E. Add orthographic_control profile block (section 2d) in computeInterpretationObject
  F. Update scorer: replace count-banding with derived_score read
  G. Add orth_det_llm_split contradiction in computeGuardrailObject
  H. Thread interpretObj into computeGuardrailObject (new 4th param)
  I. Update Tab 6 weights to 25/35/40 + add gr_rule_orth_det_llm_split toggle
  J. Tab 11: orth split indicator on teacher report row
"""

import sys

V1  = r"C:\Users\richa\Desktop\TASK ACHIEVEMENt and CONTENT QUALITY\scorer-arabic.html"
SRC = r"C:\Users\richa\Desktop\TASK ACHIEVEMENt and CONTENT QUALITY\scorer-arabic-v2.html"

# Read V1 to extract the orthography engine block (lines 6278-6620, 1-indexed)
with open(V1, 'r', encoding='utf-8') as f:
    v1_lines = f.readlines()
# V1 lines are 1-indexed in the spec; Python 0-indexed: 6277 to 6620 (inclusive)
v1_orth_block = ''.join(v1_lines[6277:6621])

with open(SRC, 'r', encoding='utf-8') as f:
    html = f.read()

original_len = html.count('\n') + 1
changes = []

# ===== A: Insert V1 engine before annotateOrthographyCode =====
OLD_A = "  function annotateOrthographyCode(response, runId) {"
V1_PREAMBLE = (
    "  // ===================================================================\n"
    "  // Tier 4G: V1 Orthographic Control engine (ported verbatim from scorer-arabic.html)\n"
    "  // computeArabicOrthography, curated lists, hasAdvancedOrthographicEvidence, ARABIC_TITLES\n"
    "  // See 04-dimension-orthographic-control.md D1, D2.\n"
    "  // ===================================================================\n"
)
NEW_A = V1_PREAMBLE + v1_orth_block + "\n  function annotateOrthographyCode(response, runId) {"
assert OLD_A in html, "A: annotateOrthographyCode marker not found"
html = html.replace(OLD_A, NEW_A, 1)
changes.append("A: V1 curated lists + hasAdvancedOrthographicEvidence + computeArabicOrthography ported")

# ===== B: Rewrite annotateOrthographyCode =====
OLD_B = """  function annotateOrthographyCode(response, runId) {
    const out = [];
    COMMON_SPELLING_ERRORS.forEach(({ wrong, right, kind }) => {
      let from = 0;
      while (true) {
        const idx = response.indexOf(wrong, from);
        if (idx < 0) break;
        out.push(makeAnnotation({
          family: 'orthography',
          type: 'orthography:common_error',
          source: 'code',
          text: wrong,
          span: { start: idx, end: idx + wrong.length },
          metadata: { kind, suggested: right },
          runId
        }));
        from = idx + wrong.length;
      }
    });
    return out;
  }"""

NEW_B = """  // annotateOrthographyCode (Tier 4G): runs computeArabicOrthography, emits per-error
  // annotations + a deterministic_snapshot sentinel for the interpretation engine (D3).
  function annotateOrthographyCode(response, runId) {
    // Helper: find the first span of a text fragment in the response.
    const findSpan = (text) => {
      const idx = response.indexOf(text);
      return idx >= 0 ? { start: idx, end: idx + text.length } : { start: 0, end: 0 };
    };

    const det = computeArabicOrthography(response, {
      allow_loanword_list: [],
      titles: ARABIC_TITLES
    });

    // Emit one annotation per curated-list flag (taa_marbuta | alif | hamza | general).
    const out = det.flags.map(f => makeAnnotation({
      family: 'orthography',
      type: 'orthography:' + f.type,
      source: 'code',
      text: f.text,
      span: findSpan(f.text),
      metadata: {
        suggested:    f.suggested,
        tier:         f.tier,
        occurrences:  f.occurrences,
        list_version: det.list_versions ? (det.list_versions[f.type] || null) : null
      },
      runId
    }));

    // Sentinel: stash the full det object so the interpretation engine can read
    // TQ / CED / letter_form_counts without re-running the engine.
    out.push(makeAnnotation({
      family: 'orthography',
      type: 'orthography:deterministic_snapshot',
      source: 'code',
      text: '',
      span: { start: 0, end: 0 },
      metadata: { snapshot: det },
      runId
    }));

    return out;
  }"""

assert OLD_B in html, "B: old annotateOrthographyCode body not found"
html = html.replace(OLD_B, NEW_B, 1)
changes.append("B: annotateOrthographyCode rewritten to use curated lists + sentinel")

# ===== C: Extend annotateOrthographyLLM =====
OLD_C = """  function annotateOrthographyLLM(response, runId) {
    const prompt = `Identify ONLY genuine spelling errors in this Arabic (MSA) response.

Orthography = HOW A WORD IS WRITTEN, not which word was chosen.

Flag only these:
- hamza placement (ء، أ، إ، ؤ، ئ) — e.g. writing إنشاء الله instead of إن شاء الله
- alif forms (ا، آ، ى) — wrong alif used
- taa marbuta vs taa vs ha (ة vs ت vs ه)
- letter substitution, missing letter, extra letter
- internal spacing within established compounds

DO NOT flag any of the following — they belong to other families:
- dialect word CHOICE (e.g. حسيت, بعدين, شفت — these are register, not orthography)
- missing MSA equivalent words (e.g. "use ذهبت instead of رحت" — this is register)
- colloquial meaning shifts (e.g. بعد used as "also/still" — this is grammar/register)
- grammar errors (agreement, conjugation, dual form — separate family)
- punctuation, capitalisation, formatting

The test: would removing the orthographic error change how the word LOOKS, not which word it is?
If the word itself is wrong-for-MSA but written correctly, do NOT flag here.

If there is no genuine WRITTEN-FORM error, return { "spelling_errors": [] }. Do not speculate. Do not invent errors.

RESPONSE:
${response}

For each genuine spelling error return:
- text: the EXACT misspelled word from the response (verbatim)
- error_subtype: "hamza" | "alif" | "taa_marbuta" | "general"
- correction: the correctly-spelled word
- note: short English explanation of what is wrong about the WRITTEN form (not the word choice)

Return JSON only:
{ "spelling_errors": [ { "text": "...", "error_subtype": "...", "correction": "...", "note": "..." }, ... ] }`;
    return llmAnnotate('orthography', prompt, response, runId, data => {
      return (data.spelling_errors || []).map(s => ({
        type: `orthography:${s.error_subtype || 'general'}`,
        text: s.text,
        metadata: { error_subtype: s.error_subtype, correction: s.correction, note: s.note }
      }));
    });
  }"""

# Build NEW_C safely avoiding raw string issues with backslash-escapes in template literals
NEW_C = (
    "  function annotateOrthographyLLM(response, runId) {\n"
    "    const prompt = `Identify ONLY genuine spelling errors in this Arabic (MSA) response, and provide a holistic orthographic accuracy score.\n"
    "\n"
    "Orthography = HOW A WORD IS WRITTEN, not which word was chosen.\n"
    "\n"
    "Flag only these:\n"
    "- hamza placement (ء، أ، إ، ؤ، ئ) — e.g. writing إنشاء الله instead of إن شاء الله\n"
    "- alif forms (ا، آ، ى) — wrong alif used\n"
    "- taa marbuta vs taa vs ha (ة vs ت vs ه)\n"
    "- letter substitution, missing letter, extra letter\n"
    "- internal spacing within established compounds\n"
    "\n"
    "DO NOT flag any of the following — they belong to other families:\n"
    "- dialect word CHOICE (e.g. حسيت, بعدين, شفت — these are register, not orthography)\n"
    "- missing MSA equivalent words (e.g. \"use ذهبت instead of رحت\" — this is register)\n"
    "- colloquial meaning shifts (e.g. بعد used as \"also/still\" — this is grammar/register)\n"
    "- grammar errors (agreement, conjugation, dual form — separate family)\n"
    "- punctuation, capitalisation, formatting\n"
    "\n"
    "The test: would removing the orthographic error change how the word LOOKS, not which word it is?\n"
    "If the word itself is wrong-for-MSA but written correctly, do NOT flag here.\n"
    "\n"
    "BANDS for llm_orthographic_accuracy_score:\n"
    "93-100  Near-native / elite control — sustained difficult environments, advanced hamza forms (ئ ؤ ء آ) used correctly in multiple positions\n"
    "87-92   Strong with advancing mastery — correct hamza in some advanced positions\n"
    "81-86   Strong stability — clean writing but avoids difficult environments OR limited advanced evidence\n"
    "61-80   Functional with notable issues\n"
    "41-60   Frequent orthographic instability\n"
    "21-40   Substantial breakdown\n"
    "0-20    Severe\n"
    "\n"
    "ABSENCE_IS_NOT_MASTERY:\n"
    "A response with no errors but no advanced orthographic evidence (rare hamza forms, sustained difficult environments) CANNOT score above 86.\n"
    "Absence of mistakes is \"Strong stability\" (81-86), not \"advancing mastery\" (87+).\n"
    "\n"
    "POSITIVE_GROUNDING_FOR_87_PLUS:\n"
    "To score 87-92 (\"Strong with advancing mastery\") at least TWO of the following must be present and cited in grounded_in:\n"
    "- Correct medial or final ئ in a non-trivial position (e.g. مسؤول، رئيس، شيئاً)\n"
    "- Correct ؤ in derived forms (e.g. مؤتمر، رؤية، مسؤولية)\n"
    "- Correct آ (alif madda) in word-initial position (e.g. آخر، آلاف، الآن)\n"
    "- Correct hamzat al-wasl vs hamzat al-qat distinction across multiple words\n"
    "- Sustained correct ة vs ه vs ت in feminine derivations across the whole response\n"
    "\n"
    "To score 93-100 (\"Near-native / elite\") the 87-92 evidence PLUS multiple advanced forms across different contexts AND no errors in difficult environments.\n"
    "\n"
    "NEGATIVE_EXAMPLE - do NOT award 87+ for:\n"
    "- An error-free response showing only basic forms (ا، ت، ة in predictable positions, no advanced hamza) → score 81-86.\n"
    "- A response that avoids difficult orthography by paraphrasing around it → cannot exceed 86.\n"
    "\n"
    "GROUNDING:\n"
    "grounded_in MUST contain verbatim Arabic phrases from the response. For any score >= 87, at least two phrases demonstrating the positive evidence above. No normalisation. No paraphrase.\n"
    "\n"
    "RESPONSE:\n"
    "${response}\n"
    "\n"
    "For each genuine spelling error return in spelling_errors:\n"
    "- text: the EXACT misspelled word from the response (verbatim)\n"
    "- error_subtype: \"hamza\" | \"alif\" | \"taa_marbuta\" | \"general\"\n"
    "- correction: the correctly-spelled word\n"
    "- note: short English explanation\n"
    "\n"
    "Return JSON only:\n"
    "{\n"
    "  \"spelling_errors\": [ { \"text\": \"...\", \"error_subtype\": \"...\", \"correction\": \"...\", \"note\": \"...\" } ],\n"
    "  \"llm_orthographic_accuracy_score\": NUMBER,\n"
    "  \"band\": \"near_native\" | \"strong_advancing\" | \"strong_stability\" | \"functional\" | \"frequent_instability\" | \"substantial_breakdown\" | \"severe\",\n"
    "  \"justification\": \"2-3 sentences grounding the score in the response\",\n"
    "  \"grounded_in\": [\"verbatim phrase 1\", \"verbatim phrase 2\"]\n"
    "}`;\n"
    "    return llmAnnotate('orthography', prompt, response, runId, data => {\n"
    "      const errors = (data.spelling_errors || []).map(s => ({\n"
    "        type: `orthography:${s.error_subtype || 'general'}`,\n"
    "        text: s.text,\n"
    "        metadata: { error_subtype: s.error_subtype, correction: s.correction, note: s.note }\n"
    "      }));\n"
    "      // Emit ceiling_score annotation carrying the LLM band score.\n"
    "      const llmScore = typeof data.llm_orthographic_accuracy_score === 'number'\n"
    "        ? data.llm_orthographic_accuracy_score : null;\n"
    "      if (llmScore !== null) {\n"
    "        errors.push({\n"
    "          type: 'orthography:ceiling_score',\n"
    "          text: '',\n"
    "          metadata: {\n"
    "            score: llmScore,\n"
    "            band: data.band || null,\n"
    "            justification: data.justification || '',\n"
    "            grounded_in: data.grounded_in || []\n"
    "          }\n"
    "        });\n"
    "      }\n"
    "      return errors;\n"
    "    });\n"
    "  }"
)

assert OLD_C in html, "C: annotateOrthographyLLM not found"
html = html.replace(OLD_C, NEW_C, 1)
changes.append("C: annotateOrthographyLLM extended with bands + grounded_in + absence-is-not-mastery + ceiling_score")

# ===== D: Update POLARITY_REGISTRY =====
OLD_D = """    // ----- orthographic_control -----
    'orthography:hamza':         { applies_to: ['orthographic_control'], polarity: 'negative' },
    'orthography:alif':          { applies_to: ['orthographic_control'], polarity: 'negative' },
    'orthography:taa_marbuta':   { applies_to: ['orthographic_control'], polarity: 'negative' },
    'orthography:general':       { applies_to: ['orthographic_control'], polarity: 'negative' },
    'orthography:common_error':  { applies_to: ['orthographic_control'], polarity: 'negative' }
  };"""

NEW_D = """    // ----- orthographic_control -----
    'orthography:hamza':                   { applies_to: ['orthographic_control'], polarity: 'negative' },
    'orthography:alif':                    { applies_to: ['orthographic_control'], polarity: 'negative' },
    'orthography:taa_marbuta':             { applies_to: ['orthographic_control'], polarity: 'negative' },
    'orthography:general':                 { applies_to: ['orthographic_control'], polarity: 'negative' },
    // common_error retired in Tier 4G — replaced by per-category types above.
    // new Tier 4G types:
    'orthography:deterministic_snapshot':  { applies_to: ['orthographic_control'], polarity: 'neutral' },
    'orthography:ceiling_score':           { applies_to: ['orthographic_control'], polarity: 'positive' }
  };"""

assert OLD_D in html, "D: POLARITY_REGISTRY orth section not found"
html = html.replace(OLD_D, NEW_D, 1)
changes.append("D: POLARITY_REGISTRY updated — common_error retired, deterministic_snapshot + ceiling_score added")

# ===== E: Add orthographic_control profile block (section 2d) in computeInterpretationObject =====
OLD_E = """    // ── 3. cap_directives ─────────────────────────────────────────────────
    const cap_directives = [];"""

NEW_E = """    // ── 2d. Orthographic Control profile (Tier 4G) ────────────────────────
    // D1/D2: read deterministic snapshot + LLM ceiling score; apply advanced-evidence cap.
    const _orthoSnap = activeAnns.find(a => a.type === 'orthography:deterministic_snapshot');
    const _det       = _orthoSnap && _orthoSnap.metadata && _orthoSnap.metadata.snapshot
                       ? _orthoSnap.metadata.snapshot : null;

    const _ceilingAnn = activeAnns.find(a => a.type === 'orthography:ceiling_score');
    const _llmRaw     = _ceilingAnn && _ceilingAnn.metadata && typeof _ceilingAnn.metadata.score === 'number'
                        ? _ceilingAnn.metadata.score : null;

    const _orthWordCount = _det
      ? (_det.letter_form_counts ? (_det.letter_form_counts.words || 0) : 0)
      : word_count;
    const _advanced = _det ? hasAdvancedOrthographicEvidence(_det.letter_form_counts) : false;

    let _llmCapped     = _llmRaw;
    let _llmCapApplied = false;
    if (!_advanced && typeof _llmRaw === 'number' && _llmRaw > 88) {
      _llmCapped     = 88;
      _llmCapApplied = true;
    }

    const _tq  = _det != null ? _det.technical_quality      : 50;
    const _ced = _det != null ? _det.common_error_detection : 50;
    const _llm = (typeof _llmCapped === 'number') ? _llmCapped : 50;

    let _orthDerived       = Math.round(_tq * 0.25 + _ced * 0.35 + _llm * 0.40);
    let _derivedCapApplied = false;
    if (!_advanced && _orthDerived > 88) {
      _orthDerived       = 88;
      _derivedCapApplied = true;
    }

    // D9: Confidence mapping for orthographic_control.
    let _orthConfidence;
    if (_orthWordCount < 10) {
      _orthConfidence = 'UNMEASURABLE';
    } else if (_orthWordCount < 30 || _llmRaw === null) {
      _orthConfidence = 'MEDIUM';
    } else {
      _orthConfidence = 'HIGH';
    }

    const _orthFlagsSummary = _det && _det.flags_summary ? _det.flags_summary : {};
    Object.assign(dp.orthographic_control, {
      technical_quality:         _tq,
      common_error_detection:    _ced,
      llm_orthographic_score:    _llm,
      llm_band:                  _ceilingAnn && _ceilingAnn.metadata ? (_ceilingAnn.metadata.band || null) : null,
      advanced_evidence_present: _advanced,
      cap_applied:               _llmCapApplied || _derivedCapApplied,
      cap_reason:                _derivedCapApplied
                                   ? 'derived_score capped at 88 — no advanced orthographic evidence'
                                   : _llmCapApplied
                                     ? 'LLM score capped at 88 — no advanced orthographic evidence'
                                     : null,
      derived_score:             _orthDerived,
      confidence:                _orthConfidence,
      evidence_summary: {
        taa_marbuta_flags: _orthFlagsSummary.taa_marbuta ? (_orthFlagsSummary.taa_marbuta.unique || 0) : 0,
        alif_flags:        _orthFlagsSummary.alif        ? (_orthFlagsSummary.alif.unique        || 0) : 0,
        hamza_flags:       _orthFlagsSummary.hamza       ? (_orthFlagsSummary.hamza.unique       || 0) : 0,
        general_flags:     _orthFlagsSummary.general     ? (_orthFlagsSummary.general.unique     || 0) : 0,
        llm_errors:        activeAnns.filter(a =>
          ['orthography:hamza','orthography:alif','orthography:taa_marbuta','orthography:general'].includes(a.type)
          && a.source === 'llm').length
      }
    });

    // ── 3. cap_directives ─────────────────────────────────────────────────
    const cap_directives = [];"""

assert OLD_E in html, "E: cap_directives header not found"
html = html.replace(OLD_E, NEW_E, 1)
changes.append("E: orthographic_control profile block (section 2d) added to computeInterpretationObject")

# ===== F: Update scorer — replace count-banding with derived_score read =====
OLD_F = """    // ── Orthographic Control ─────────────────────────────────
    // Tier 4A: match the prefixed types orthography:common_error / :hamza / :alif / :taa_marbuta / :general.
    const orthoAll  = annotations.filter(a => a.family === 'orthography');
    const orthoCode = orthoAll.filter(a => a.source === 'code' || a.type === 'orthography:common_error');
    const orthoLLM  = orthoAll.filter(a => a.source === 'llm'  || ['orthography:hamza','orthography:alif','orthography:taa_marbuta','orthography:general'].includes(a.type));

    const TQ_BAND        = [100, 90, 75, 60, 45, 30];
    const tq_score       = TQ_BAND[Math.min(orthoAll.length,  5)] !== undefined ? TQ_BAND[Math.min(orthoAll.length,  5)] : 20;
    const CED_BAND       = [100, 85, 65, 45];
    const ced_score      = CED_BAND[Math.min(orthoCode.length, 3)] !== undefined ? CED_BAND[Math.min(orthoCode.length, 3)] : 25;
    const LLM_ORTHO_BAND = [100, 80, 60, 40];
    const llm_ortho      = LLM_ORTHO_BAND[Math.min(orthoLLM.length, 3)] !== undefined ? LLM_ORTHO_BAND[Math.min(orthoLLM.length, 3)] : 20;

    const orthoW    = sw.orthographic_control || { technical_quality: 40, common_error_detection: 30, llm: 30 };
    const ortho_dim = Math.min(100, Math.round(
      tq_score  * (orthoW.technical_quality      / 100) +
      ced_score * (orthoW.common_error_detection / 100) +
      llm_ortho * (orthoW.llm                    / 100)
    ));"""

NEW_F = """    // ── Orthographic Control ─────────────────────────────────
    // Tier 4G: interpretation-driven — reads derived_score from InterpretationObject (D6).
    // Legacy count-banding retired. Scorer does NOT apply caps (interpretation engine owns them).
    const orthProfile = interpretObj
      && interpretObj.dimension_profiles
      && interpretObj.dimension_profiles.orthographic_control;

    let ortho_dim, tq_score, ced_score, llm_ortho;
    if (orthProfile && typeof orthProfile.derived_score === 'number') {
      ortho_dim = orthProfile.derived_score;
      tq_score  = orthProfile.technical_quality      != null ? orthProfile.technical_quality      : 50;
      ced_score = orthProfile.common_error_detection != null ? orthProfile.common_error_detection : 50;
      llm_ortho = orthProfile.llm_orthographic_score != null ? orthProfile.llm_orthographic_score : 50;
    } else {
      // Legacy fallback — count-banding (pre-Tier-4G or interpretObj unavailable).
      const orthoAll  = annotations.filter(a => a.family === 'orthography');
      const orthoCode = orthoAll.filter(a => a.source === 'code');
      const orthoLLM  = orthoAll.filter(a => a.source === 'llm');
      const TQ_BAND        = [100, 90, 75, 60, 45, 30];
      const CED_BAND       = [100, 85, 65, 45];
      const LLM_ORTHO_BAND = [100, 80, 60, 40];
      tq_score  = TQ_BAND[Math.min(orthoAll.length,  5)]        !== undefined ? TQ_BAND[Math.min(orthoAll.length,  5)]        : 20;
      ced_score = CED_BAND[Math.min(orthoCode.length, 3)]        !== undefined ? CED_BAND[Math.min(orthoCode.length, 3)]        : 25;
      llm_ortho = LLM_ORTHO_BAND[Math.min(orthoLLM.length, 3)]  !== undefined ? LLM_ORTHO_BAND[Math.min(orthoLLM.length, 3)]  : 20;
      const orthoW = sw.orthographic_control || { technical_quality: 25, common_error_detection: 35, llm: 40 };
      ortho_dim = Math.min(100, Math.round(
        tq_score  * (orthoW.technical_quality      / 100) +
        ced_score * (orthoW.common_error_detection / 100) +
        llm_ortho * (orthoW.llm                    / 100)
      ));
    }"""

assert OLD_F in html, "F: old orthographic scorer block not found"
html = html.replace(OLD_F, NEW_F, 1)
changes.append("F: scorer reads derived_score from InterpretationObject for orthographic_control")

# ===== G: Add orth_det_llm_split contradiction rule =====
OLD_G = "    // Per-dimension confidence — added v0.3 Tab 11 build."

NEW_G = (
    "    // Tier 4G (D9a): orth_det_llm_split contradiction — MODERATE severity.\n"
    "    // Reads from interpretObj (4th param). Teacher-visible only (Tab 10/11); no auto-correction.\n"
    "    if (rules.orth_det_llm_split !== false) {\n"
    "      const _orp = interpretObj && interpretObj.dimension_profiles && interpretObj.dimension_profiles.orthographic_control;\n"
    "      if (_orp && typeof _orp.technical_quality === 'number' && typeof _orp.llm_orthographic_score === 'number') {\n"
    "        const detCombined = Math.round(_orp.technical_quality * (25/60) + _orp.common_error_detection * (35/60));\n"
    "        const llmScore    = _orp.llm_orthographic_score;\n"
    "        const split       = Math.abs(detCombined - llmScore);\n"
    "        if (split > 25) {\n"
    "          contradictions.push({\n"
    "            rule:      'orth_det_llm_split',\n"
    "            severity:  'MODERATE',\n"
    "            dimension: 'orthographic_control',\n"
    "            message:   'Orthographic Control deterministic engine (' + detCombined + ') and LLM judgement (' + llmScore + ') disagree by ' + split + ' points. Combined derived_score uses both — review which view better matches the response.',\n"
    "            data:      { det_combined: detCombined, llm_score: llmScore, split: split, derived_score: _orp.derived_score }\n"
    "          });\n"
    "          confidence_per_dimension.orthographic_control = 'MEDIUM';\n"
    "        }\n"
    "      }\n"
    "    }\n"
    "\n"
    "    // Per-dimension confidence — added v0.3 Tab 11 build."
)

assert OLD_G in html, "G: per-dimension confidence comment not found"
html = html.replace(OLD_G, NEW_G, 1)
changes.append("G: orth_det_llm_split contradiction rule added (MODERATE severity, D9a)")

# ===== H: Thread interpretObj into computeGuardrailObject (4th param) =====
OLD_H1 = "  function computeGuardrailObject(scoreObj, annotations, guardrailConfig) {"
NEW_H1 = "  function computeGuardrailObject(scoreObj, annotations, guardrailConfig, interpretObj) {"
assert OLD_H1 in html, "H1: computeGuardrailObject signature not found"
html = html.replace(OLD_H1, NEW_H1, 1)

OLD_H2 = "      const guardrailObj = computeGuardrailObject(scoreObj, allAnnotations, grCfg);"
NEW_H2 = "      const guardrailObj = computeGuardrailObject(scoreObj, allAnnotations, grCfg, interpretObj);"
assert OLD_H2 in html, "H2: guardrail call site not found"
html = html.replace(OLD_H2, NEW_H2, 1)
changes.append("H: interpretObj threaded into computeGuardrailObject as 4th param")

# ===== I1-I3: Tab 6 sub-weight defaults: 40/30/30 -> 25/35/40 =====
OLD_I1 = 'value="40" /><span class="cal-weight-unit">%</span>'
NEW_I1 = 'value="25" /><span class="cal-weight-unit">%</span>'
# Need unique context — use the id attribute
OLD_I1_FULL = 'id="sw_ortho_tq"  min="0" max="100" step="0.1" value="40" /><span class="cal-weight-unit">%</span>'
NEW_I1_FULL = 'id="sw_ortho_tq"  min="0" max="100" step="0.1" value="25" /><span class="cal-weight-unit">%</span>'
assert OLD_I1_FULL in html, "I1: sw_ortho_tq input not found"
html = html.replace(OLD_I1_FULL, NEW_I1_FULL, 1)

OLD_I2_FULL = 'id="sw_ortho_ced" min="0" max="100" step="0.1" value="30" /><span class="cal-weight-unit">%</span>'
NEW_I2_FULL = 'id="sw_ortho_ced" min="0" max="100" step="0.1" value="35" /><span class="cal-weight-unit">%</span>'
assert OLD_I2_FULL in html, "I2: sw_ortho_ced input not found"
html = html.replace(OLD_I2_FULL, NEW_I2_FULL, 1)

OLD_I3_FULL = 'id="sw_ortho_llm" min="0" max="100" step="0.1" value="30" /><span class="cal-weight-unit">%</span>'
NEW_I3_FULL = 'id="sw_ortho_llm" min="0" max="100" step="0.1" value="40" /><span class="cal-weight-unit">%</span>'
assert OLD_I3_FULL in html, "I3: sw_ortho_llm input not found"
html = html.replace(OLD_I3_FULL, NEW_I3_FULL, 1)
changes.append("I1-3: Tab 6 ortho weights updated to 25/35/40")

# ===== I4: Add gr_rule_orth_det_llm_split toggle after gr_rule_coherence_connectives row =====
OLD_I4 = (
    '          <input type="checkbox" id="gr_rule_coherence_connectives" checked>\n'
    '          <span class="toggle-slider"></span>\n'
    '        </label>\n'
    '      </div>\n'
    '    </div>'
)
NEW_I4 = (
    '          <input type="checkbox" id="gr_rule_coherence_connectives" checked>\n'
    '          <span class="toggle-slider"></span>\n'
    '        </label>\n'
    '      </div>\n'
    '      <div class="gr-toggle-row">\n'
    '        <div>\n'
    '          <div class="gr-toggle-label">Det / LLM split — Ortho</div>\n'
    '          <div class="gr-toggle-desc">Deterministic engine and LLM orthography judgement disagree by &gt;25 points — flag for teacher review</div>\n'
    '        </div>\n'
    '        <label class="toggle-switch">\n'
    '          <input type="checkbox" id="gr_rule_orth_det_llm_split" checked>\n'
    '          <span class="toggle-slider"></span>\n'
    '        </label>\n'
    '      </div>\n'
    '    </div>'
)
assert OLD_I4 in html, "I4: gr_rule_coherence_connectives toggle row close not found"
html = html.replace(OLD_I4, NEW_I4, 1)
changes.append("I4: gr_rule_orth_det_llm_split toggle added to Tab 6")

# ===== I5: Add orth_det_llm_split to default state contradiction_rules =====
OLD_I5 = (
    '    contradiction_rules: {\n'
    '      high_grammar_low_orthography: true,\n'
    '      dialect_dominant_high_accuracy: true,\n'
    '      high_coherence_no_connectives: true\n'
    '    }\n'
    '  };'
)
NEW_I5 = (
    '    contradiction_rules: {\n'
    '      high_grammar_low_orthography: true,\n'
    '      dialect_dominant_high_accuracy: true,\n'
    '      high_coherence_no_connectives: true,\n'
    '      orth_det_llm_split: true\n'
    '    }\n'
    '  };'
)
assert OLD_I5 in html, "I5: default contradiction_rules block not found"
html = html.replace(OLD_I5, NEW_I5, 1)
changes.append("I5: orth_det_llm_split: true added to default guardrailConfig")

# ===== I6: Add orth_det_llm_split to _readGrConfig =====
OLD_I6 = (
    '      contradiction_rules: {\n'
    '        high_grammar_low_orthography:  document.getElementById(\'gr_rule_grammar_ortho\').checked,\n'
    '        dialect_dominant_high_accuracy: document.getElementById(\'gr_rule_dialect_accuracy\').checked,\n'
    '        high_coherence_no_connectives:  document.getElementById(\'gr_rule_coherence_connectives\').checked\n'
    '      }\n'
    '    };'
)
NEW_I6 = (
    '      contradiction_rules: {\n'
    '        high_grammar_low_orthography:  document.getElementById(\'gr_rule_grammar_ortho\').checked,\n'
    '        dialect_dominant_high_accuracy: document.getElementById(\'gr_rule_dialect_accuracy\').checked,\n'
    '        high_coherence_no_connectives:  document.getElementById(\'gr_rule_coherence_connectives\').checked,\n'
    '        orth_det_llm_split:             document.getElementById(\'gr_rule_orth_det_llm_split\').checked\n'
    '      }\n'
    '    };'
)
assert OLD_I6 in html, "I6: _readGrConfig contradiction_rules block not found"
html = html.replace(OLD_I6, NEW_I6, 1)
changes.append("I6: _readGrConfig reads gr_rule_orth_det_llm_split")

# ===== I7: Add orth_det_llm_split to _populateGrForm =====
OLD_I7 = (
    "    setChk('gr_rule_grammar_ortho',          r.high_grammar_low_orthography);\n"
    "    setChk('gr_rule_dialect_accuracy',       r.dialect_dominant_high_accuracy);\n"
    "    setChk('gr_rule_coherence_connectives',  r.high_coherence_no_connectives);\n"
    "  }"
)
NEW_I7 = (
    "    setChk('gr_rule_grammar_ortho',          r.high_grammar_low_orthography);\n"
    "    setChk('gr_rule_dialect_accuracy',       r.dialect_dominant_high_accuracy);\n"
    "    setChk('gr_rule_coherence_connectives',  r.high_coherence_no_connectives);\n"
    "    setChk('gr_rule_orth_det_llm_split',     r.orth_det_llm_split);\n"
    "  }"
)
assert OLD_I7 in html, "I7: _populateGrForm setChk block not found"
html = html.replace(OLD_I7, NEW_I7, 1)
changes.append("I7: _populateGrForm populates gr_rule_orth_det_llm_split")

# ===== J: Tab 11 teacher report — orth_det_llm_split indicator on orthographic_control row =====
# Insert after the language_accuracy block closing brace, before dimRowsHtml +=
OLD_J = (
    "      }\n"
    "      dimRowsHtml +=\n"
    "        '<tr>' +"
)
NEW_J = (
    "      }\n"
    "      // Tier 4G (D9a): orthographic_control — orth_det_llm_split indicator (teacher report only).\n"
    "      if (dim === 'orthographic_control') {\n"
    "        const go_contradictions = go.contradictions || [];\n"
    "        if (go_contradictions.some(c => c.rule === 'orth_det_llm_split')) {\n"
    "          if (notesHtml.startsWith('<span style=\"color:var(--muted)')) notesHtml = '';\n"
    "          notesHtml += '<span class=\"tr-note-pill warning\">⚠ deterministic/LLM split</span>';\n"
    "        }\n"
    "      }\n"
    "      dimRowsHtml +=\n"
    "        '<tr>' +"
)
assert OLD_J in html, "J: dimRowsHtml insertion point not found"
html = html.replace(OLD_J, NEW_J, 1)
changes.append("J: Tab 11 teacher report: orth_det_llm_split indicator added for orthographic_control row")

# ===== Write =====
with open(SRC, 'w', encoding='utf-8') as f:
    f.write(html)

final_len = html.count('\n') + 1
print(f"Read: {original_len} lines")
for i, c in enumerate(changes, 1):
    print(f"  {i}: {c}")
print(f"Written: {final_len} lines ({final_len - original_len:+d})")
print("Done.")
