#!/usr/bin/env python3
# tmp_tier4i.py — Tier 4I (Language Range) patch for scorer-arabic-v2.html
# Uses assert OLD in html / html.replace(OLD, NEW, 1) pattern.

import sys
import os

SRC = r"C:\Users\richa\Desktop\TASK ACHIEVEMENt and CONTENT QUALITY\scorer-arabic-v2.html"
V1  = r"C:\Users\richa\Desktop\TASK ACHIEVEMENt and CONTENT QUALITY\scorer-arabic.html"

print("Reading files...")
with open(SRC, 'r', encoding='utf-8') as f:
    html = f.read()
with open(V1, 'r', encoding='utf-8') as f:
    v1_lines = f.read().splitlines()

print(f"V2 file: {len(html)} chars, {html.count(chr(10))+1} lines")

# ─────────────────────────────────────────────────────────────────────────────
# Change A1 — rename function
# ─────────────────────────────────────────────────────────────────────────────
OLD_A1 = '  function annotateRangeLLM(response, runId) {'
NEW_A1 = '  function annotateRangeEvidence(response, runId) {'
assert OLD_A1 in html, "FAIL A1: function rename anchor not found"
html = html.replace(OLD_A1, NEW_A1, 1)
print("A1 done: annotateRangeLLM -> annotateRangeEvidence")

# ─────────────────────────────────────────────────────────────────────────────
# Change A2 — rename emitted type inside the function
# ─────────────────────────────────────────────────────────────────────────────
OLD_A2 = "        type: `range:${r.subtype || 'finding'}`,"
NEW_A2 = "        type: 'range:' + (r.subtype || 'finding') + '_evidence',"
assert OLD_A2 in html, "FAIL A2: emitted type anchor not found"
html = html.replace(OLD_A2, NEW_A2, 1)
print("A2 done: emitted type updated")

# ─────────────────────────────────────────────────────────────────────────────
# Change B — Insert three new scoring annotators BEFORE annotateRangeEvidence
# ─────────────────────────────────────────────────────────────────────────────
# Get V1 prompt lines (0-indexed line numbers, using splitlines())
# vocabPrompt: V1 lines 3931:3994 (0-indexed) → lines[3931] through lines[3993]
# morphPrompt: V1 lines 3995:4048 (0-indexed) → lines[3995] through lines[4047]
# sentencePrompt: V1 lines 4049:4107 (0-indexed) → lines[4049] through lines[4106]

vocab_v1_lines  = v1_lines[3931:3994]   # includes the `const vocabPrompt = \`` line and closing `\`;`
morph_v1_lines  = v1_lines[3995:4048]
sentence_v1_lines = v1_lines[4049:4107]

# We need the raw prompt body — the content between the opening backtick and
# the closing backtick `};`.  Strip the JS wrapper lines.
# The V1 lines start with e.g.:
#   "  const vocabPrompt = `You are ..."  (line 3931 in V1, i.e. index 3931)
# and end with:
#   "  </inputs>`;"  (last line of the block)
#
# We'll extract just the lines between (and including) the opening line content
# and closing, but we only need the PROMPT TEXT — what's inside the backtick string.
# Strategy: join them, then strip JS wrappers to get raw prompt text.

def extract_prompt_body(lines):
    """Return the raw template literal body (everything between opening ` and closing `)."""
    joined = '\n'.join(lines)
    # Find first backtick
    start = joined.index('`')
    # Find last backtick
    end = joined.rindex('`')
    return joined[start+1:end]

vocab_body    = extract_prompt_body(vocab_v1_lines)
morph_body    = extract_prompt_body(morph_v1_lines)
sentence_body = extract_prompt_body(sentence_v1_lines)

# ── Grounding / Construct Purity / Annotation Discipline V2 additions ─────────
# These are appended to each prompt AFTER </output_format> block, BEFORE <inputs>

COMMON_GROUNDING = '''
GROUNDING:
Score MUST cite verbatim Arabic phrases from the response in the "grounded_in" array.
Phrases must appear in the response exactly as quoted (no normalisation of hamza, alif, taa marbuta).'''

VOCAB_CONSTRUCT_PURITY = '''
CONSTRUCT PURITY:
Dialect forms (Levantine, Gulf, Egyptian, Maghrebi, Iraqi, Sudanese) do NOT count as positive evidence of vocabulary diversity. Examples that DO NOT count:
كيطل، زوين، حوايج، خويا، بزاف
Note dialect forms as informal markers in the justification but they cannot drive a band above 60.

ANNOTATION DISCIPLINE:
A feature must stand out from the response\'s OWN baseline to merit citation.
Use observational language (signals/shows/marks — NOT creates/weaves/captures).'''

MORPH_CONSTRUCT_PURITY = '''
CONSTRUCT PURITY:
Dialect forms (Levantine, Gulf, Egyptian, Maghrebi, Iraqi, Sudanese) do NOT count as positive evidence of morphological variety. Examples that DO NOT count:
dialect verb morphology (كنوقفو، كنهدرو، كيطل prefix forms)
Note dialect forms as informal markers in the justification but they cannot drive a band above 60.

ANNOTATION DISCIPLINE:
A feature must stand out from the response\'s OWN baseline to merit citation.
Use observational language (signals/shows/marks — NOT creates/weaves/captures).'''

SENTENCE_CONSTRUCT_PURITY = '''
CONSTRUCT PURITY:
Dialect forms (Levantine, Gulf, Egyptian, Maghrebi, Iraqi, Sudanese) do NOT count as positive evidence of sentence complexity. Examples that DO NOT count:
ملي، باش، فاش، حتى قبل ما
Note dialect forms as informal markers in the justification but they cannot drive a band above 60.

ANNOTATION DISCIPLINE:
A feature must stand out from the response\'s OWN baseline to merit citation.
Use observational language (signals/shows/marks — NOT creates/weaves/captures).'''

VOCAB_GENRE_CAP = '''
TASK_TYPE_AWARE_CAP_EXCEPTION:
The cap on recycled content verbs (cap 30) is genre-sensitive.
- For task_type in {narrative, email, account, recount}: recycled travel/motion/consumption verbs are genre-appropriate. Raise the recycled-verb cap to 40 for these task types only. Other vocab caps (basic_everyday, narrow_scope, identical_vocabulary) still apply normally.
- For task_type in {argumentative, descriptive, report, explanatory}: the cap 30 stays — recycled verbs signal genuine vocabulary weakness.
<task_type>${taskType}</task_type>
Use the task_type tag above when deciding whether the recycled-verb cap applies at 30 or 40.'''

# ── New V2 output schemas ──────────────────────────────────────────────────────
VOCAB_OUTPUT_FORMAT = '''{
  "vocabulary_diversity_score": NUMBER | null,
  "band": "extremely_limited"|"very_limited"|"limited"|"moderate"|"good"|"strong"|"exceptional",
  "justification": "2-3 sentences. Quote 2-3 verbatim Arabic phrases.",
  "grounded_in": ["verbatim phrase 1", "verbatim phrase 2"],
  "cap_applied": null | "basic_everyday" | "narrow_scope" | "identical_vocabulary" | "recycled_verbs" | "recycled_verbs_genre_exempt" | "fewer_than_10_distinct"
}'''

MORPH_OUTPUT_FORMAT = '''{
  "morphological_variety_score": NUMBER | null,
  "band": "extremely_limited"|"very_limited"|"limited"|"moderate"|"good"|"strong"|"exceptional",
  "justification": "2-3 sentences.",
  "grounded_in": ["verbatim phrase 1", ...],
  "cap_applied": null | "only_isolated_words" | "same_simple_past_throughout" | "only_one_two_derived" | "same_handful_repeated"
}'''

SENTENCE_OUTPUT_FORMAT = '''{
  "arabic_sentence_complexity_score": NUMBER | null,
  "band": "extremely_limited"|"very_limited"|"limited"|"moderate"|"good"|"strong"|"exceptional",
  "justification": "2-3 sentences.",
  "grounded_in": ["verbatim phrase 1", ...],
  "cap_applied": null | "all_fragments_under_4" | "identical_svo" | "simple_svo_chained" | "coordination_only" | "single_subordinate"
}'''

def insert_v2_additions_vocab(body):
    """Insert V2 grounding/purity additions and replace output_format in vocab body."""
    # Replace the old output_format block
    old_of_start = '<output_format>'
    old_of_end   = '</output_format>'
    start_idx = body.index(old_of_start)
    end_idx   = body.index(old_of_end) + len(old_of_end)
    old_of_block = body[start_idx:end_idx]
    new_of_block = (
        '<output_format>\n'
        'Return exactly:\n'
        + VOCAB_OUTPUT_FORMAT + '\n'
        + 'No extra keys. No markdown fences.\n'
        + VOCAB_GENRE_CAP + '\n'
        + '</output_format>'
    )
    body = body[:start_idx] + new_of_block + body[end_idx:]
    # Insert V2 additions just before <inputs>
    inputs_idx = body.index('<inputs>')
    v2_add = COMMON_GROUNDING + '\n' + VOCAB_CONSTRUCT_PURITY + '\n'
    body = body[:inputs_idx] + v2_add + '\n' + body[inputs_idx:]
    return body

def insert_v2_additions_morph(body):
    """Insert V2 grounding/purity additions and replace output_format in morph body."""
    old_of_start = '<output_format>'
    old_of_end   = '</output_format>'
    start_idx = body.index(old_of_start)
    end_idx   = body.index(old_of_end) + len(old_of_end)
    new_of_block = (
        '<output_format>\n'
        'Return exactly:\n'
        + MORPH_OUTPUT_FORMAT + '\n'
        + 'No extra keys. No markdown fences.\n'
        + '</output_format>'
    )
    body = body[:start_idx] + new_of_block + body[end_idx:]
    inputs_idx = body.index('<inputs>')
    v2_add = COMMON_GROUNDING + '\n' + MORPH_CONSTRUCT_PURITY + '\n'
    body = body[:inputs_idx] + v2_add + '\n' + body[inputs_idx:]
    return body

def insert_v2_additions_sentence(body):
    """Insert V2 grounding/purity additions and replace output_format in sentence body."""
    old_of_start = '<output_format>'
    old_of_end   = '</output_format>'
    start_idx = body.index(old_of_start)
    end_idx   = body.index(old_of_end) + len(old_of_end)
    new_of_block = (
        '<output_format>\n'
        'Return exactly:\n'
        + SENTENCE_OUTPUT_FORMAT + '\n'
        + 'No extra keys. No markdown fences.\n'
        + '</output_format>'
    )
    body = body[:start_idx] + new_of_block + body[end_idx:]
    inputs_idx = body.index('<inputs>')
    v2_add = COMMON_GROUNDING + '\n' + SENTENCE_CONSTRUCT_PURITY + '\n'
    body = body[:inputs_idx] + v2_add + '\n' + body[inputs_idx:]
    return body

vocab_body_v2    = insert_v2_additions_vocab(vocab_body)
morph_body_v2    = insert_v2_additions_morph(morph_body)
sentence_body_v2 = insert_v2_additions_sentence(sentence_body)

# ── Build the three new annotator functions ────────────────────────────────────

NEW_B = r"""  // ── annotateVocabularyDiversity (Tier 4I) ──────────────────────────────────
  // Scores vocabulary diversity from V1 vocabPrompt + V2 grounding/purity additions.
  // Takes (response, taskObj, runId) — needs taskObj.task_type for genre cap.
  async function annotateVocabularyDiversity(response, taskObj, runId) {
    const TASHKEEL = /[ً-ٰٟۖ-ۭ]/g;
    const wc = (response || '').replace(TASHKEEL, '').trim().split(/\s+/).filter(x => x).length;
    const q  = taskObj || {};
    const taskType = (taskObj && taskObj.task_type) || 'unknown';
    const prompt = `""" + vocab_body_v2 + r"""`;
    return llmAnnotate('vocab_diversity', prompt, response, runId, data => {
      if (data.score === null && data.reason) return [];
      const score = (typeof data.vocabulary_diversity_score === 'number') ? data.vocabulary_diversity_score : null;
      return [{
        family: 'range',
        type: 'range:vocabulary_score',
        source: 'llm',
        text: '',
        span: { start: 0, end: response.length },
        metadata: {
          score:         score,
          band:          data.band          || null,
          justification: data.justification || '',
          grounded_in:   data.grounded_in   || [],
          cap_applied:   data.cap_applied   || null
        }
      }];
    });
  }

  // ── annotateMorphologicalVariety (Tier 4I) ───────────────────────────────────
  // Scores morphological variety from V1 morphPrompt + V2 grounding/purity additions.
  async function annotateMorphologicalVariety(response, runId) {
    const TASHKEEL = /[ً-ٰٟۖ-ۭ]/g;
    const wc = (response || '').replace(TASHKEEL, '').trim().split(/\s+/).filter(x => x).length;
    const q  = {};
    const prompt = `""" + morph_body_v2 + r"""`;
    return llmAnnotate('morph_variety', prompt, response, runId, data => {
      if (data.score === null && data.reason) return [];
      const score = (typeof data.morphological_variety_score === 'number') ? data.morphological_variety_score : null;
      return [{
        family: 'range',
        type: 'range:morphology_score',
        source: 'llm',
        text: '',
        span: { start: 0, end: response.length },
        metadata: {
          score:         score,
          band:          data.band          || null,
          justification: data.justification || '',
          grounded_in:   data.grounded_in   || [],
          cap_applied:   data.cap_applied   || null
        }
      }];
    });
  }

  // ── annotateSentenceComplexity (Tier 4I) ─────────────────────────────────────
  // Scores Arabic sentence complexity from V1 sentencePrompt + V2 grounding/purity additions.
  async function annotateSentenceComplexity(response, runId) {
    const TASHKEEL = /[ً-ٰٟۖ-ۭ]/g;
    const wc = (response || '').replace(TASHKEEL, '').trim().split(/\s+/).filter(x => x).length;
    const q  = {};
    const prompt = `""" + sentence_body_v2 + r"""`;
    return llmAnnotate('sentence_complexity', prompt, response, runId, data => {
      if (data.score === null && data.reason) return [];
      const score = (typeof data.arabic_sentence_complexity_score === 'number') ? data.arabic_sentence_complexity_score : null;
      return [{
        family: 'range',
        type: 'range:sentence_complexity_score',
        source: 'llm',
        text: '',
        span: { start: 0, end: response.length },
        metadata: {
          score:         score,
          band:          data.band          || null,
          justification: data.justification || '',
          grounded_in:   data.grounded_in   || [],
          cap_applied:   data.cap_applied   || null
        }
      }];
    });
  }

"""

OLD_B_ANCHOR = '  function annotateRangeEvidence(response, runId) {'
assert OLD_B_ANCHOR in html, "FAIL B: annotateRangeEvidence anchor not found for insertion"
html = html.replace(OLD_B_ANCHOR, NEW_B + OLD_B_ANCHOR, 1)
print("B done: three new scoring annotators inserted")

# ─────────────────────────────────────────────────────────────────────────────
# Change C — Update POLARITY_REGISTRY for range family
# ─────────────────────────────────────────────────────────────────────────────
OLD_C = """    // ----- language_range -----
    'range:vocabulary':          { applies_to: ['language_range'], polarity: 'positive' },
    'range:morphology':          { applies_to: ['language_range'], polarity: 'positive' },
    'range:sentence_complexity': { applies_to: ['language_range'], polarity: 'positive' },
    'range:descriptive_control': { applies_to: ['language_range'], polarity: 'positive' },
    'range:elaboration':         { applies_to: ['language_range'], polarity: 'positive' },
    'range:lexical_density':     { applies_to: ['language_range'], polarity: 'neutral' },"""

NEW_C = """    // ----- language_range -----
    // Tier 4I: three scoring annotators (positive) + diagnostic evidence types (neutral_diagnostic).
    'range:vocabulary_score':              { applies_to: ['language_range'], polarity: 'positive' },
    'range:morphology_score':              { applies_to: ['language_range'], polarity: 'positive' },
    'range:sentence_complexity_score':     { applies_to: ['language_range'], polarity: 'positive' },
    'range:vocabulary_evidence':           { applies_to: ['language_range'], polarity: 'neutral_diagnostic' },
    'range:morphology_evidence':           { applies_to: ['language_range'], polarity: 'neutral_diagnostic' },
    'range:sentence_complexity_evidence':  { applies_to: ['language_range'], polarity: 'neutral_diagnostic' },
    'range:descriptive_control_evidence':  { applies_to: ['language_range'], polarity: 'neutral_diagnostic' },
    'range:elaboration_evidence':          { applies_to: ['language_range'], polarity: 'neutral_diagnostic' },
    // Legacy range types (pre-Tier-4I); keep for backward compat but demote polarity:
    'range:vocabulary':          { applies_to: ['language_range'], polarity: 'neutral_diagnostic' },
    'range:morphology':          { applies_to: ['language_range'], polarity: 'neutral_diagnostic' },
    'range:sentence_complexity': { applies_to: ['language_range'], polarity: 'neutral_diagnostic' },
    'range:descriptive_control': { applies_to: ['language_range'], polarity: 'neutral_diagnostic' },
    'range:elaboration':         { applies_to: ['language_range'], polarity: 'neutral_diagnostic' },
    'range:lexical_density':     { applies_to: ['language_range'], polarity: 'neutral' },"""

assert OLD_C in html, "FAIL C: POLARITY_REGISTRY anchor not found"
html = html.replace(OLD_C, NEW_C, 1)
print("C done: POLARITY_REGISTRY updated")

# ─────────────────────────────────────────────────────────────────────────────
# Change D — Add computeInterpretationObject section 2f
# ─────────────────────────────────────────────────────────────────────────────
OLD_D = """        // ── 3. cap_directives ─────────────────────────────────────────────────
    const cap_directives = [];"""

NEW_D_SECTION = """    // ── 2f. Language Range profile (Tier 4I) ──────────────────────────────────
    // D3/D6: read three scoring annotations; apply dialect-dominant soft cap (D7).
    const vAnn_lr = activeAnns.find(a => a.type === 'range:vocabulary_score');
    const mAnn_lr = activeAnns.find(a => a.type === 'range:morphology_score');
    const sAnn_lr = activeAnns.find(a => a.type === 'range:sentence_complexity_score');

    const v_lr = vAnn_lr && vAnn_lr.metadata && typeof vAnn_lr.metadata.score === 'number' ? vAnn_lr.metadata.score : null;
    const m_lr = mAnn_lr && mAnn_lr.metadata && typeof mAnn_lr.metadata.score === 'number' ? mAnn_lr.metadata.score : null;
    const s_lr = sAnn_lr && sAnn_lr.metadata && typeof sAnn_lr.metadata.score === 'number' ? sAnn_lr.metadata.score : null;

    let lr_derived = null;
    let lr_ceiling_applied = null;
    let lr_ceiling_source  = null;
    if (typeof v_lr === 'number' && typeof m_lr === 'number' && typeof s_lr === 'number') {
      lr_derived = Math.round(v_lr * 0.334 + m_lr * 0.333 + s_lr * 0.333);

      // D7 soft cap — dialect-dominant on MSA target.
      // Preferred: S&R profile; Fallback: global_profile; Last resort: skip.
      const sr_lr = dp.style_register;
      let lr_dialectDominant = false;
      let lr_formalMsaTarget = false;

      if (sr_lr && (sr_lr.dominant_register || sr_lr.dialect_density != null)) {
        lr_dialectDominant = sr_lr.dominant_register === 'dialect_dominant';
        lr_formalMsaTarget = (sr_lr.target_register === 'formal_msa') || (sr_lr.target_register == null);
        lr_ceiling_source  = 'style_register_profile';
      } else if (global_profile && (global_profile.dominant_register || global_profile.dialect_density != null)) {
        lr_dialectDominant = global_profile.dominant_register === 'dialect_dominant'
                          || (global_profile.dialect_density != null && global_profile.dialect_density >= 0.10);
        lr_formalMsaTarget = true;
        lr_ceiling_source  = 'global_profile_fallback';
      } else {
        lr_ceiling_source  = 'no_register_signal';
      }

      if (lr_dialectDominant && lr_formalMsaTarget && lr_derived > 60) {
        lr_derived         = 60;
        lr_ceiling_applied = 'dialect_dominant_soft_cap_60';
      }
    }

    // D8 confidence
    const lr_nullCount = [v_lr, m_lr, s_lr].filter(x => x === null).length;
    let lr_confidence;
    if (word_count < 30) {
      lr_confidence = 'UNMEASURABLE';
    } else if (lr_nullCount >= 2) {
      lr_confidence = 'LOW';
    } else if (lr_nullCount === 1) {
      lr_confidence = 'MEDIUM';
    } else {
      lr_confidence = 'HIGH';
    }

    const lr_ldAnn  = activeAnns.find(a => a.type === 'range:lexical_density');
    const lr_ldVal  = lr_ldAnn && lr_ldAnn.metadata ? (lr_ldAnn.metadata.density || null) : null;
    const lr_diagCount = activeAnns.filter(a =>
      ['range:vocabulary_evidence','range:morphology_evidence','range:sentence_complexity_evidence',
       'range:descriptive_control_evidence','range:elaboration_evidence'].includes(a.type)).length;

    Object.assign(dp.language_range, {
      vocabulary_diversity_score:  v_lr,
      vocabulary_diversity_band:   vAnn_lr && vAnn_lr.metadata ? (vAnn_lr.metadata.band || null) : null,
      vocabulary_diversity_cap:    vAnn_lr && vAnn_lr.metadata ? (vAnn_lr.metadata.cap_applied || null) : null,
      morphological_variety_score: m_lr,
      morphological_variety_band:  mAnn_lr && mAnn_lr.metadata ? (mAnn_lr.metadata.band || null) : null,
      morphological_variety_cap:   mAnn_lr && mAnn_lr.metadata ? (mAnn_lr.metadata.cap_applied || null) : null,
      sentence_complexity_score:   s_lr,
      sentence_complexity_band:    sAnn_lr && sAnn_lr.metadata ? (sAnn_lr.metadata.band || null) : null,
      sentence_complexity_cap:     sAnn_lr && sAnn_lr.metadata ? (sAnn_lr.metadata.cap_applied || null) : null,
      derived_score:               lr_derived,
      ceiling_applied:             lr_ceiling_applied,
      ceiling_source:              lr_ceiling_source,
      confidence:                  lr_confidence,
      evidence_summary: {
        vocabulary_grounded_in:          vAnn_lr && vAnn_lr.metadata ? (vAnn_lr.metadata.grounded_in || []) : [],
        morphology_grounded_in:          mAnn_lr && mAnn_lr.metadata ? (mAnn_lr.metadata.grounded_in || []) : [],
        sentence_complexity_grounded_in: sAnn_lr && sAnn_lr.metadata ? (sAnn_lr.metadata.grounded_in || []) : [],
        diagnostic_annotation_count:     lr_diagCount,
        lexical_density:                 lr_ldVal
      }
    });

        // ── 3. cap_directives ─────────────────────────────────────────────────
    const cap_directives = [];"""

assert OLD_D in html, "FAIL D: cap_directives anchor not found"
html = html.replace(OLD_D, NEW_D_SECTION, 1)
print("D done: section 2f language_range profile inserted")

# ─────────────────────────────────────────────────────────────────────────────
# Change E — Update scorer Range branch
# ─────────────────────────────────────────────────────────────────────────────
OLD_E = """    // ── Language Range ───────────────────────────────────────
    // Tier 4A: exclude the lexical_density annotation from the strength-sum by matching the
    // prefixed type — the previous bare-suffix `!== 'lexical_density'` test was always true
    // (since 'range:lexical_density' !== 'lexical_density'), so the density annotation was
    // double-counted into range_raw.
    const STRENGTH_MAP = { modest: 10, clear: 25, strong: 40 };
    const rangeAnns    = annotations.filter(a => a.family === 'range' && a.type !== 'range:lexical_density');
    let range_raw = 0;
    for (const ann of rangeAnns) {
      range_raw += STRENGTH_MAP[(ann.metadata && ann.metadata.strength)] || 10;
    }
    range_raw = Math.min(100, range_raw);

    const ldAnn = annotations.find(a => a.family === 'range' && a.type === 'range:lexical_density');
    let lr_dim;
    if (rangeAnns.length === 0 && ldAnn) {
      lr_dim = Math.min(100, Math.round(((ldAnn.metadata && ldAnn.metadata.density) || 0) * 100));
    } else if (ldAnn) {
      const ld_s = Math.min(100, Math.round(((ldAnn.metadata && ldAnn.metadata.density) || 0) * 100));
      lr_dim = Math.round(range_raw * 0.8 + ld_s * 0.2);
    } else {
      lr_dim = range_raw;
    }"""

NEW_E = """    // ── Language Range ───────────────────────────────────────
    // Tier 4I: reads derived_score from InterpretationObject.
    const rangeProfile = interpretObj
      && interpretObj.dimension_profiles
      && interpretObj.dimension_profiles.language_range;

    let lr_dim;
    if (rangeProfile && typeof rangeProfile.derived_score === 'number') {
      lr_dim = rangeProfile.derived_score;
    } else if (rangeProfile && rangeProfile.derived_score === null) {
      lr_dim = null;   // N/A*
    } else {
      // Legacy fallback — strength-sum + lexical_density (pre-Tier-4I or interpretObj unavailable).
      const rangeAnns = annotations.filter(a => a.family === 'range' && a.type !== 'range:lexical_density');
      const STRENGTH_MAP = { modest: 10, clear: 25, strong: 40 };
      let range_raw = 0;
      for (const ann of rangeAnns) {
        range_raw += STRENGTH_MAP[(ann.metadata && ann.metadata.strength)] || 10;
      }
      range_raw = Math.min(100, range_raw);
      const ldAnn = annotations.find(a => a.family === 'range' && a.type === 'range:lexical_density');
      if (rangeAnns.length === 0 && ldAnn) {
        lr_dim = Math.min(100, Math.round(((ldAnn.metadata && ldAnn.metadata.density) || 0) * 100));
      } else if (ldAnn) {
        const ld_s = Math.min(100, Math.round(((ldAnn.metadata && ldAnn.metadata.density) || 0) * 100));
        lr_dim = Math.round(range_raw * 0.8 + ld_s * 0.2);
      } else {
        lr_dim = range_raw;
      }
    }"""

assert OLD_E in html, "FAIL E: Range scorer block anchor not found"
html = html.replace(OLD_E, NEW_E, 1)
print("E done: scorer Range branch updated")

# ─────────────────────────────────────────────────────────────────────────────
# Change F — Update DIMENSION_ROUTING.language_range
# ─────────────────────────────────────────────────────────────────────────────
OLD_F = "    language_range:         'unmeasurable-pulled-to-centre',"
NEW_F = "    language_range:         'measurable-with-ceiling',"
assert OLD_F in html, "FAIL F: DIMENSION_ROUTING anchor not found"
html = html.replace(OLD_F, NEW_F, 1)
print("F done: DIMENSION_ROUTING updated")

# ─────────────────────────────────────────────────────────────────────────────
# Change G — Update runLLMAnnotators
# ─────────────────────────────────────────────────────────────────────────────
OLD_G = "      _runAnnotatorWithStatus('range',           () => annotateRangeLLM(response, runId)),"
NEW_G = """      _runAnnotatorWithStatus('range_evidence',  () => annotateRangeEvidence(response, runId)),
      _runAnnotatorWithStatus('vocab_diversity', () => annotateVocabularyDiversity(response, taskObj, runId)),
      _runAnnotatorWithStatus('morph_variety',   () => annotateMorphologicalVariety(response, runId)),
      _runAnnotatorWithStatus('sentence_complexity', () => annotateSentenceComplexity(response, runId)),"""
assert OLD_G in html, "FAIL G: runLLMAnnotators anchor not found"
html = html.replace(OLD_G, NEW_G, 1)
print("G done: runLLMAnnotators updated")

# ─────────────────────────────────────────────────────────────────────────────
# Write output
# ─────────────────────────────────────────────────────────────────────────────
with open(SRC, 'w', encoding='utf-8') as f:
    f.write(html)

final_lines = html.count('\n') + 1
print(f"\nSUCCESS: {SRC}")
print(f"Final line count: {final_lines}")

# ── Verification checks ────────────────────────────────────────────────────────
checks = {
    'annotateVocabularyDiversity':        'annotateVocabularyDiversity' in html,
    'annotateMorphologicalVariety':       'annotateMorphologicalVariety' in html,
    'annotateSentenceComplexity':         'annotateSentenceComplexity' in html,
    'annotateRangeEvidence':              'annotateRangeEvidence' in html,
    'annotateRangeLLM gone':              'annotateRangeLLM' not in html,
    'range:vocabulary_score':             'range:vocabulary_score' in html,
    'range:morphology_score':             'range:morphology_score' in html,
    'range:sentence_complexity_score':    'range:sentence_complexity_score' in html,
    'range:vocabulary_evidence':          'range:vocabulary_evidence' in html,
    'measurable-with-ceiling (lr)':       "language_range:         'measurable-with-ceiling'" in html,
    'vocab_diversity in runLLMAnnotators':'vocab_diversity' in html,
    'lr_derived in computeInterpret':     'lr_derived' in html,
}

print("\nVerification:")
all_pass = True
for k, v in checks.items():
    status = "PASS" if v else "FAIL"
    if not v:
        all_pass = False
    print(f"  {status}: {k}")

if all_pass:
    print("\nAll checks PASSED.")
else:
    print("\nSome checks FAILED — review output above.")
    sys.exit(1)
