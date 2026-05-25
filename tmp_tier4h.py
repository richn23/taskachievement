#!/usr/bin/env python3
"""
Tier 4H patch script — Organisation & Coherence upgrade.
Reads scorer-arabic-v2.html, applies all changes A–M, writes back.
"""

import sys
import re

SRC = r"C:\Users\richa\Desktop\TASK ACHIEVEMENt and CONTENT QUALITY\scorer-arabic-v2.html"
V1  = r"C:\Users\richa\Desktop\TASK ACHIEVEMENt and CONTENT QUALITY\scorer-arabic.html"

print("Reading V2 source…")
with open(SRC, encoding="utf-8") as f:
    html = f.read()
orig_lines = html.count("\n")
print(f"  V2: {orig_lines} lines")

print("Reading V1 source…")
with open(V1, encoding="utf-8") as f:
    v1_lines = f.readlines()
print(f"  V1: {len(v1_lines)} lines")

def apply(tag, old, new, src):
    assert old in src, f"[{tag}] ANCHOR NOT FOUND:\n{repr(old[:120])}"
    result = src.replace(old, new, 1)
    assert result != src, f"[{tag}] replace had no effect"
    print(f"  [{tag}] OK")
    return result

# ─────────────────────────────────────────────────────────────────
# Read V1 blocks
# ─────────────────────────────────────────────────────────────────

# A: computeArabicCohesiveDevices (V1 lines 3057–3180, 0-indexed = lines[3057:3181])
v1_compute_block = "".join(v1_lines[3057:3181])

# C: coherenceFlowPrompt text (V1 lines 4110–4203, 0-indexed = lines[4110:4204])
v1_cf_prompt_lines = v1_lines[4110:4204]
v1_cf_prompt_raw = "".join(v1_cf_prompt_lines)

# Extract just the prompt content (strip outer JS, keep template literal content)
# V1 wraps it as: const coherenceFlowPrompt = `...`;
# We want everything between the first backtick and the last closing backtick+semicolon
# but we need to RE-build V2 version with updated output_format and new grounding sections.

# Extract V1 prompt body (between first ` and final `;)
prompt_start = v1_cf_prompt_raw.index("`") + 1
prompt_end   = v1_cf_prompt_raw.rindex("`")
v1_prompt_body = v1_cf_prompt_raw[prompt_start:prompt_end]

# In V1 the output_format block is:
OLD_OUTPUT_FORMAT = """\
<output_format>
Return exactly:
{
  "coherence_flow_score": NUMBER,
  "justification": "2-3 sentences explaining the score. Refer specifically to how ideas progress (or fail to progress). Quote 1-2 short phrases showing where progression succeeds or breaks down. Do NOT comment on vividness, style, or grammar."
}
No extra keys. No markdown fences.
</output_format>"""

NEW_OUTPUT_FORMAT = """\
<output_format>
Return exactly:
{
  "coherence_flow_score": NUMBER | null,
  "band": "strong_progression" | "clear_progression" | "some_progression" | "weak_progression" | "no_progression",
  "justification": "2-3 sentences. Quote 1-2 verbatim Arabic phrases.",
  "grounded_in": ["verbatim phrase 1"],
  "cap_applied": null | "sequencing_only" | "arbitrary_paragraphs" | "topic_shifts"
}
No extra keys. No markdown fences.
</output_format>

GROUNDING:
Score MUST cite verbatim Arabic phrases from the response in the "grounded_in" array.
Phrases must appear in the response exactly as quoted. No normalisation of hamza/alif/taa marbuta. No paraphrase.

GROUNDED_IN EVIDENCE TYPES — cite examples from MULTIPLE categories, not just one.
A coherence judgement grounded entirely in temporal markers is undersupported.

1. TEMPORAL / SEQUENCING — markers that order events in time.
2. CAUSAL DEVELOPMENT — markers that link cause to effect, premise to conclusion.
   Required for clear/strong progression in argumentative/explanatory tasks.
3. THEMATIC CONTINUITY — reuse or development of a topic across paragraphs.
4. REFERENTIAL LINKAGE — pronouns, demonstratives binding sentences to earlier content.

For scores >= 61, grounded_in SHOULD contain evidence from at least two of these four categories.
For scores >= 81, grounded_in SHOULD contain evidence from at least three categories AND demonstrate paragraph-level cohesion.

CONSTRUCT PURITY:
Dialect-form connectives (\\u0645\\u0644\\u064a\\u060c \\u0628\\u0627\\u0634\\u060c \\u0641\\u0627\\u0634\\u060c \\u0645\\u0646 \\u0628\\u0639\\u062f\\u060c etc.) cannot serve as evidence of formal coherence control. They may carry meaning but do NOT qualify as "MSA coherence control" evidence. Distinguish: "response IS coherent" (judge holistically) vs "grounded_in shows MSA evidence" (MSA forms only).
A pure-dialect response with strong logical progression may land 51–65 based on holistic judgement; above 65 requires MSA-form evidence in grounded_in."""

assert OLD_OUTPUT_FORMAT in v1_prompt_body, "V1 output_format block not found in prompt body"
v2_prompt_body = v1_prompt_body.replace(OLD_OUTPUT_FORMAT, NEW_OUTPUT_FORMAT, 1)

# Build the full annotateCoherenceFlow function
ANNOTATE_COHERENCE_FLOW = """\
  // ── annotateCoherenceFlow (Tier 4H) ──────────────────────────────────────────
  // Holistic coherence & flow LLM annotator.  Emits cohesion:coherence_flow_score.
  // Built on V1 coherenceFlowPrompt (lines 4111-4203) with V2 output schema.
  async function annotateCoherenceFlow(response, taskObj, runId) {
    const TASHKEEL = /[\\u064B-\\u065F\\u0670\\u06D6-\\u06ED]/g;
    const wc = (response || '').replace(TASHKEEL, '').trim().split(/\\s+/).filter(x => x).length;
    const q  = taskObj || {};
    const prompt = `""" + v2_prompt_body + """\`;
    return llmAnnotate('cohesion', prompt, response, runId, data => {
      return [{
        family: 'cohesion',
        type:   'cohesion:coherence_flow_score',
        source: 'llm',
        text:   '',
        span:   { start: 0, end: response.length },
        metadata: {
          score:        (typeof data.coherence_flow_score === 'number') ? data.coherence_flow_score : null,
          band:         data.band        || null,
          justification:data.justification || '',
          grounded_in:  data.grounded_in  || [],
          cap_applied:  data.cap_applied  || null
        }
      }];
    });
  }

"""
print("  [C-prep] annotateCoherenceFlow function built OK")

# ─────────────────────────────────────────────────────────────────
# Change A: Insert computeArabicCohesiveDevices from V1 before annotateCohesionCode
# ─────────────────────────────────────────────────────────────────
A_ANCHOR = "  function annotateCohesionCode(response, runId) {"

A_INSERT = (
    "  // ============================================================\n"
    "  // computeArabicCohesiveDevices — ported verbatim from V1\n"
    "  // (V1 lines 3058–3180). Deterministic connective tally.\n"
    "  // ============================================================\n"
    + v1_compute_block
    + "\n"
    + A_ANCHOR
)

html = apply("A", A_ANCHOR, A_INSERT, html)

# ─────────────────────────────────────────────────────────────────
# Change B: Rewrite annotateCohesionCode
# ─────────────────────────────────────────────────────────────────
B_OLD = """  function annotateCohesionCode(response, runId) {
    const out = [];
    ARABIC_CONNECTIVES.forEach(conn => {
      // word-ish boundary: whitespace/punctuation/start/end of string
      const re = new RegExp(`(?:^|[\\\\s.،,;؛])(${conn.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&')})(?=[\\\\s.،,;؛]|$)`, 'g');
      let m;
      while ((m = re.exec(response)) !== null) {
        const start = m.index + (m[0].length - m[1].length);
        const end = start + m[1].length;
        out.push(makeAnnotation({
          family: 'cohesion',
          type: 'cohesion:connective',
          source: 'code',
          text: m[1],
          span: { start, end },
          metadata: { connective: conn },
          runId
        }));
      }
    });
    return out;
  }"""

B_NEW = """  // annotateCohesionCode (Tier 4H): wraps computeArabicCohesiveDevices.
  // Emits per-match cohesion:device annotations + cohesion:deterministic_snapshot sentinel.
  function annotateCohesionCode(response, runId) {
    const det = computeArabicCohesiveDevices(response);
    if (det.score === null) return [];   // 30-word floor

    const findSpan = (text) => {
      const idx = response.indexOf(text);
      return idx >= 0 ? { start: idx, end: idx + text.length } : { start: 0, end: 0 };
    };

    const out = [];
    for (const [cat, matches] of Object.entries(det.category_breakdown || {})) {
      for (const m of matches) {
        out.push(makeAnnotation({
          family: 'cohesion',
          type: 'cohesion:device',
          source: 'code',
          text: m.conn,
          span: findSpan(m.conn),
          metadata: {
            category: cat,
            base_form: m.conn,
            has_clitic_prefix: false,
            occurrences_in_response: m.count
          },
          runId
        }));
      }
    }

    // Sentinel: full det object for interpretation engine (TQ/CED/category_breakdown)
    out.push(makeAnnotation({
      family: 'cohesion',
      type: 'cohesion:deterministic_snapshot',
      source: 'code',
      text: '',
      span: { start: 0, end: 0 },
      metadata: { snapshot: det },
      runId
    }));

    return out;
  }"""

html = apply("B", B_OLD, B_NEW, html)

# ─────────────────────────────────────────────────────────────────
# Change C: Insert annotateCoherenceFlow before annotateCohesionLLM
# ─────────────────────────────────────────────────────────────────
C_ANCHOR = "  function annotateCohesionLLM(response, runId) {"

C_INSERT = ANNOTATE_COHERENCE_FLOW + C_ANCHOR

html = apply("C", C_ANCHOR, C_INSERT, html)

# ─────────────────────────────────────────────────────────────────
# Change D: Rename cohesion:${c.subtype||'finding'} -> cohesion:llm_observation
# ─────────────────────────────────────────────────────────────────
D_OLD = "        type: `cohesion:${c.subtype || 'finding'}`,"
D_NEW = "        type: 'cohesion:llm_observation',"

html = apply("D", D_OLD, D_NEW, html)

# ─────────────────────────────────────────────────────────────────
# Change E: Update POLARITY_REGISTRY for cohesion family
# ─────────────────────────────────────────────────────────────────
E_OLD = """    // ----- organisation_coherence -----
    'cohesion:connective':       { applies_to: ['organisation_coherence'], polarity: 'positive' },
    'cohesion:transition':       { applies_to: ['organisation_coherence'], polarity: 'positive' },
    'cohesion:discourse_marker': { applies_to: ['organisation_coherence'], polarity: 'positive' },"""

E_NEW = """    // ----- organisation_coherence -----
    // Tier 4H: per-match device + holistic flow. Old bare types retired.
    'cohesion:device':                 { applies_to: ['organisation_coherence'], polarity: 'positive' },
    'cohesion:deterministic_snapshot': { applies_to: ['organisation_coherence'], polarity: 'neutral_diagnostic' },
    'cohesion:coherence_flow_score':   { applies_to: ['organisation_coherence'], polarity: 'positive' },
    'cohesion:llm_observation':        { applies_to: ['organisation_coherence'], polarity: 'neutral_diagnostic' },
    // Legacy types retired Tier 4H (kept for audit; no longer driver):
    'cohesion:connective':             { applies_to: ['organisation_coherence'], polarity: 'neutral_diagnostic' },
    'cohesion:transition':             { applies_to: ['organisation_coherence'], polarity: 'neutral_diagnostic' },
    'cohesion:discourse_marker':       { applies_to: ['organisation_coherence'], polarity: 'neutral_diagnostic' },"""

html = apply("E", E_OLD, E_NEW, html)

# ─────────────────────────────────────────────────────────────────
# Change F: Add computeInterpretationObject section 2e
# ─────────────────────────────────────────────────────────────────
F_ANCHOR = "    // ── 3. cap_directives ─────────────────────────────────────────────────"

F_INSERT = """\
    // ── 2e. Organisation & Coherence profile (Tier 4H) ────────────────────────
    // D1/D2: read deterministic snapshot + holistic coherence flow LLM score.
    const cohSnap = activeAnns.find(a => a.type === 'cohesion:deterministic_snapshot');
    const cohDet  = cohSnap && cohSnap.metadata && cohSnap.metadata.snapshot
                    ? cohSnap.metadata.snapshot : null;

    const cfAnn   = activeAnns.find(a => a.type === 'cohesion:coherence_flow_score');
    const cfScore = cfAnn && cfAnn.metadata && typeof cfAnn.metadata.score === 'number'
                    ? cfAnn.metadata.score : null;
    const cfBand  = cfAnn && cfAnn.metadata ? (cfAnn.metadata.band || null) : null;
    const cfCap   = cfAnn && cfAnn.metadata ? (cfAnn.metadata.cap_applied || null) : null;

    const cd_oc = cohDet != null ? cohDet.score : 50;
    const cf_oc = (typeof cfScore === 'number') ? cfScore : 50;
    const _ocDerived = Math.round(cd_oc * 0.30 + cf_oc * 0.70);

    // D8 confidence
    let _ocConf;
    if (word_count < 30) {
      _ocConf = 'UNMEASURABLE';
    } else if ((word_count >= 30 && word_count <= 60) || (cohDet && cohDet.distinct_types === 0) || cfScore === null) {
      _ocConf = 'MEDIUM';
    } else {
      _ocConf = 'HIGH';
    }

    Object.assign(dp.organisation_coherence, {
      cohesive_devices_score:     cd_oc,
      cohesive_devices_breakdown: {
        categories:    cohDet ? (cohDet.connective_category_count || 0) : 0,
        distinct_types: cohDet ? (cohDet.distinct_types || 0) : 0,
        per_100_words:  cohDet ? (cohDet.arabic_connectives_per_100_words || null) : null
      },
      coherence_flow_score:       cf_oc,
      coherence_flow_band:        cfBand,
      coherence_flow_cap_applied: cfCap,
      derived_score:              _ocDerived,
      confidence:                 _ocConf,
      evidence_summary: {
        device_count:               activeAnns.filter(a => a.type === 'cohesion:device').length,
        category_count:             cohDet ? (cohDet.connective_category_count || 0) : 0,
        distinct_types:             cohDet ? (cohDet.distinct_types || 0) : 0,
        coherence_flow_grounded_in: cfAnn && cfAnn.metadata ? (cfAnn.metadata.grounded_in || []) : []
      }
    });

    """ + F_ANCHOR

html = apply("F", F_ANCHOR, F_INSERT, html)

# ─────────────────────────────────────────────────────────────────
# Change G: Update scorer OC branch (lines 6593-6610 area)
# ─────────────────────────────────────────────────────────────────
G_OLD = """    // ── Organisation & Coherence ─────────────────────────────
    const cohAnns     = annotations.filter(a => a.family === 'cohesion');
    const cohCount    = cohAnns.length;
    const cohSubtypes = new Set(cohAnns.map(a => (a.metadata && a.metadata.subtype) || a.type).filter(Boolean));
    const cohSubCount = cohSubtypes.size;

    const COUNT_BAND  = [0, 20, 40, 60, 75, 85, 95];
    const count_score = COUNT_BAND[Math.min(cohCount, 5)] !== undefined ? COUNT_BAND[Math.min(cohCount, 5)] : 95;

    const SUBTYPE_BAND  = [20, 40, 70, 90];
    const subtype_score = SUBTYPE_BAND[Math.min(cohSubCount, 3)] !== undefined ? SUBTYPE_BAND[Math.min(cohSubCount, 3)] : 90;

    const ocW    = sw.organisation_coherence || { cohesive_devices: 50, coherence_flow: 50 };
    const oc_dim = Math.min(100, Math.round(
      count_score   * (ocW.cohesive_devices / 100) +
      subtype_score * (ocW.coherence_flow   / 100)
    ));"""

G_NEW = """    // ── Organisation & Coherence ─────────────────────────────
    // Tier 4H: reads derived_score from InterpretationObject.
    const ocProfile = interpretObj
      && interpretObj.dimension_profiles
      && interpretObj.dimension_profiles.organisation_coherence;

    let oc_dim, count_score, subtype_score;
    if (ocProfile && typeof ocProfile.derived_score === 'number') {
      oc_dim       = ocProfile.derived_score;
      count_score   = ocProfile.cohesive_devices_score != null ? ocProfile.cohesive_devices_score : 50;
      subtype_score = ocProfile.coherence_flow_score   != null ? ocProfile.coherence_flow_score   : 50;
    } else {
      // Legacy fallback — count-banding (pre-Tier-4H or interpretObj unavailable).
      const cohAnns     = annotations.filter(a => a.family === 'cohesion');
      const cohCount    = cohAnns.length;
      const cohSubtypes = new Set(cohAnns.map(a => (a.metadata && a.metadata.subtype) || a.type).filter(Boolean));
      const cohSubCount = cohSubtypes.size;
      const COUNT_BAND  = [0, 20, 40, 60, 75, 85, 95];
      const SUBTYPE_BAND = [20, 40, 70, 90];
      count_score   = COUNT_BAND[Math.min(cohCount, 5)]    !== undefined ? COUNT_BAND[Math.min(cohCount, 5)]    : 95;
      subtype_score = SUBTYPE_BAND[Math.min(cohSubCount, 3)] !== undefined ? SUBTYPE_BAND[Math.min(cohSubCount, 3)] : 90;
      const ocW    = sw.organisation_coherence || { cohesive_devices: 30, coherence_flow: 70 };
      oc_dim = Math.min(100, Math.round(
        count_score   * (ocW.cohesive_devices / 100) +
        subtype_score * (ocW.coherence_flow   / 100)
      ));
    }"""

html = apply("G", G_OLD, G_NEW, html)

# ─────────────────────────────────────────────────────────────────
# Change H: Add annotateCoherenceFlow to runLLMAnnotators
# ─────────────────────────────────────────────────────────────────
H_OLD = "      _runAnnotatorWithStatus('cohesion',        () => annotateCohesionLLM(response, runId)),"
H_NEW = ("      _runAnnotatorWithStatus('cohesion',        () => annotateCohesionLLM(response, runId)),\n"
         "      _runAnnotatorWithStatus('coherence_flow',  () => annotateCoherenceFlow(response, taskObj, runId)),")

html = apply("H", H_OLD, H_NEW, html)

# ─────────────────────────────────────────────────────────────────
# Change I: Add coh_dev_flow_split contradiction rule + add taskObject param
# ─────────────────────────────────────────────────────────────────

# Step I.1: Update computeGuardrailObject signature to add taskObject param
I1_OLD = "  function computeGuardrailObject(scoreObj, annotations, guardrailConfig, interpretObj) {"
I1_NEW = "  function computeGuardrailObject(scoreObj, annotations, guardrailConfig, interpretObj, taskObject) {"

html = apply("I1", I1_OLD, I1_NEW, html)

# Step I.2: Update the call site to pass taskObj
I2_OLD = "      const guardrailObj = computeGuardrailObject(scoreObj, allAnnotations, grCfg, interpretObj);"
I2_NEW = "      const guardrailObj = computeGuardrailObject(scoreObj, allAnnotations, grCfg, interpretObj, taskObj);"

html = apply("I2", I2_OLD, I2_NEW, html)

# Step I.3: Insert contradiction rule before Per-dimension confidence
I3_OLD = "    // Per-dimension confidence — added v0.3 Tab 11 build."
I3_NEW = """\
    // Tier 4H (D8a): coh_dev_flow_split — task-type-aware severity.
    if (rules.coh_dev_flow_split !== false) {
      const _ocp = interpretObj && interpretObj.dimension_profiles && interpretObj.dimension_profiles.organisation_coherence;
      if (_ocp && typeof _ocp.cohesive_devices_score === 'number' && typeof _ocp.coherence_flow_score === 'number') {
        const cd = _ocp.cohesive_devices_score;
        const cf = _ocp.coherence_flow_score;
        const split = Math.abs(cd - cf);
        if (split > 40) {
          const NARRATIVE_LIKE_TYPES = new Set(['narrative', 'email', 'account', 'recount', 'description']);
          const taskType = (taskObject && taskObject.task_type) || 'unknown';
          const isNarrativeLike = NARRATIVE_LIKE_TYPES.has(taskType);
          const severity = isNarrativeLike ? 'WARNING' : 'MODERATE';
          contradictions.push({
            rule:      'coh_dev_flow_split',
            severity,
            dimension: 'organisation_coherence',
            message:   'Cohesive Devices (' + cd + ') and Coherence & Flow (' + cf + ') disagree by ' + split + ' pts' +
                       (isNarrativeLike
                         ? ' — ' + taskType + ' task type, narrative-genre split is often normal, treat as warning.'
                         : ' — review which view is correct.'),
            data: { cd, cf, split, task_type: taskType, severity_basis: isNarrativeLike ? 'narrative_genre' : 'default' }
          });
          if (severity === 'MODERATE') {
            confidence_per_dimension.organisation_coherence = 'MEDIUM';
          }
        }
      }
    }

    """ + I3_OLD

html = apply("I3", I3_OLD, I3_NEW, html)

# ─────────────────────────────────────────────────────────────────
# Change J: Update OC sub-weight defaults to 30/70
# ─────────────────────────────────────────────────────────────────
J_OLD = "    oc:    { cohesive: 50, flow: 50 },"
J_NEW = "    oc:    { cohesive: 30, flow: 70 },"

html = apply("J", J_OLD, J_NEW, html)

# Also update the HTML input default values from 50/50 to 30/70
J2_OLD = ('            <input type="number" class="cal-weight-input sub-w-input" data-group="oc" id="sw_oc_cohesive" '
          'min="0" max="100" step="0.1" value="50" />')
J2_NEW = ('            <input type="number" class="cal-weight-input sub-w-input" data-group="oc" id="sw_oc_cohesive" '
          'min="0" max="100" step="0.1" value="30" />')

html = apply("J2", J2_OLD, J2_NEW, html)

J3_OLD = ('            <input type="number" class="cal-weight-input sub-w-input" data-group="oc" id="sw_oc_flow"     '
          'min="0" max="100" step="0.1" value="50" />')
J3_NEW = ('            <input type="number" class="cal-weight-input sub-w-input" data-group="oc" id="sw_oc_flow"     '
          'min="0" max="100" step="0.1" value="70" />')

html = apply("J3", J3_OLD, J3_NEW, html)

# ─────────────────────────────────────────────────────────────────
# Change K: Tab 6: add gr_rule_coh_dev_flow_split toggle
# ─────────────────────────────────────────────────────────────────
K_OLD = (
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

K_NEW = (
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
    '      <div class="gr-toggle-row">\n'
    '        <div>\n'
    '          <div class="gr-toggle-label">Cohesive Devices / Flow split — OC</div>\n'
    '          <div class="gr-toggle-desc">Cohesive Devices score and Coherence &amp; Flow score disagree by &gt;40 points — flag for teacher review (severity depends on task type)</div>\n'
    '        </div>\n'
    '        <label class="toggle-switch">\n'
    '          <input type="checkbox" id="gr_rule_coh_dev_flow_split" checked>\n'
    '          <span class="toggle-slider"></span>\n'
    '        </label>\n'
    '      </div>\n'
    '    </div>'
)

html = apply("K", K_OLD, K_NEW, html)

# ─────────────────────────────────────────────────────────────────
# Change L: Update _readGrConfig, GR_DEFAULTS, _populateGrForm
# ─────────────────────────────────────────────────────────────────

# L1: GR_DEFAULTS
L1_OLD = "      orth_det_llm_split: true\n    }"
L1_NEW = "      orth_det_llm_split: true,\n      coh_dev_flow_split: true\n    }"

html = apply("L1", L1_OLD, L1_NEW, html)

# L2: _readGrConfig
L2_OLD = "        orth_det_llm_split:             document.getElementById('gr_rule_orth_det_llm_split').checked\n      }"
L2_NEW = ("        orth_det_llm_split:             document.getElementById('gr_rule_orth_det_llm_split').checked,\n"
          "        coh_dev_flow_split:              document.getElementById('gr_rule_coh_dev_flow_split').checked\n"
          "      }")

html = apply("L2", L2_OLD, L2_NEW, html)

# L3: _populateGrForm
L3_OLD = "    setChk('gr_rule_orth_det_llm_split',     r.orth_det_llm_split);"
L3_NEW = ("    setChk('gr_rule_orth_det_llm_split',     r.orth_det_llm_split);\n"
          "    setChk('gr_rule_coh_dev_flow_split',      r.coh_dev_flow_split);")

html = apply("L3", L3_OLD, L3_NEW, html)

# ─────────────────────────────────────────────────────────────────
# Change M: Tab 11: coh_dev_flow_split indicator on OC row
# ─────────────────────────────────────────────────────────────────
M_OLD = ("      // Tier 4G (D9a): orthographic_control — orth_det_llm_split indicator (teacher report only).\n"
         "      if (dim === 'orthographic_control') {\n"
         "        const go_contradictions = go.contradictions || [];\n"
         "        if (go_contradictions.some(c => c.rule === 'orth_det_llm_split')) {\n"
         "          if (notesHtml.startsWith('<span style=\"color:var(--muted)')) notesHtml = '';\n"
         "          notesHtml += '<span class=\"tr-note-pill warning\">⚠ deterministic/LLM split</span>';\n"
         "        }\n"
         "      }")

M_NEW = ("      // Tier 4G (D9a): orthographic_control — orth_det_llm_split indicator (teacher report only).\n"
         "      if (dim === 'orthographic_control') {\n"
         "        const go_contradictions = go.contradictions || [];\n"
         "        if (go_contradictions.some(c => c.rule === 'orth_det_llm_split')) {\n"
         "          if (notesHtml.startsWith('<span style=\"color:var(--muted)')) notesHtml = '';\n"
         "          notesHtml += '<span class=\"tr-note-pill warning\">⚠ deterministic/LLM split</span>';\n"
         "        }\n"
         "      }\n"
         "      // Tier 4H (D8a): organisation_coherence — coh_dev_flow_split indicator (teacher report only).\n"
         "      if (dim === 'organisation_coherence') {\n"
         "        const go_contradictions = go.contradictions || [];\n"
         "        if (go_contradictions.some(c => c.rule === 'coh_dev_flow_split')) {\n"
         "          if (notesHtml.startsWith('<span style=\"color:var(--muted)')) notesHtml = '';\n"
         "          notesHtml += '<span class=\"tr-note-pill warning\">⚠ coh.dev/flow split</span>';\n"
         "        }\n"
         "      }")

html = apply("M", M_OLD, M_NEW, html)

# ─────────────────────────────────────────────────────────────────
# Write output
# ─────────────────────────────────────────────────────────────────
print("\nWriting updated V2…")
with open(SRC, "w", encoding="utf-8") as f:
    f.write(html)

new_lines = html.count("\n")
print(f"  Done. Lines: {orig_lines} -> {new_lines} (+{new_lines - orig_lines})")

# ─────────────────────────────────────────────────────────────────
# Verification checks
# ─────────────────────────────────────────────────────────────────
print("\nVerification checks:")
checks = [
    'computeArabicCohesiveDevices',
    'cohesion:deterministic_snapshot',
    'cohesion:coherence_flow_score',
    'annotateCoherenceFlow',
    'cohesion:device',
    'cohesion:llm_observation',
    'coh_dev_flow_split',
    'gr_rule_coh_dev_flow_split',
]
all_ok = True
for c in checks:
    present = c in html
    status = "OK" if present else "MISSING"
    if not present:
        all_ok = False
    print(f"  {'[OK]' if present else '[FAIL]'} {c}")

if all_ok:
    print("\nAll checks passed. Tier 4H applied successfully.")
else:
    print("\nSome checks FAILED — review output above.")
    sys.exit(1)
