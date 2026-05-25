"""
Tier 4J — Content Quality anti-fabrication discipline.
Changes:
  A. annotateCQ prompt: evidence_text → evidence_spans[], add EVIDENCE RULE
  B. annotateCQ annotation builder: emit evidence_spans + grounded_in, backwards-compat fallback
  C. Verifier comment update (evidence_text → evidence_spans)
  D. Add _normaliseArabic helper + Pass 4 (CQ evidence verification with normalisation tolerance)
  E. computeInterpretationObject section 2g: CQ profile (enforcement + density caps + dp.content_quality)
  F. computeScoreObject CQ branch: reads derived_score from interpretObj
  G. computeGuardrailObject: cq_evidence_reuse contradiction rule
  H. Tab 6 HTML: gr_rule_cq_evidence_reuse toggle
  I. GR_DEFAULTS, _readGrConfig, _populateGrForm: wired toggle
  J. Tab 11: CQ enforcement events + normalisation footnote
"""

SRC = r"C:\Users\richa\Desktop\TASK ACHIEVEMENt and CONTENT QUALITY\scorer-arabic-v2.html"

with open(SRC, 'r', encoding='utf-8') as f:
    html = f.read()

original_len = html.count('\n') + 1
changes = []

# ── Change A: annotateCQ prompt schema update ────────────────────────────────
OLD_A = """For each requirement return:
- requirement_id: integer (0-indexed)
- score: 0, 1, 2, or 3
- evidence_text: the EXACT sentence(s) from the response that justify the score (verbatim). Empty string if score is 0.
- justification: 1 sentence explaining the score

Return JSON only:
{ "cq_scores": [ { "requirement_id": 0, "score": 2, "evidence_text": "...", "justification": "..." }, ... ] }`;"""

NEW_A = """EVIDENCE RULE:
- evidence_spans is an array of verbatim sentences from the response.
- A score of 1 requires ≥1 span naming the topic.
- A score of 2 requires ≥1 span demonstrating development (topic + reason, detail, or example).
- A score of 3 requires ≥2 spans OR one substantial span demonstrating extended development.
- If you cannot quote verbatim spans, the score MUST be 0.
- Fragments under 7 words cannot support a score ≥2.
- Fragments under 12 words with total under 15 cannot support a score of 3.
- Empty evidence_spans with score ≥1 will be force-corrected to 0 downstream.

For each requirement return:
- requirement_id: integer (0-indexed)
- score: 0, 1, 2, or 3
- evidence_spans: array of verbatim sentences from the response (empty array if score = 0)
- justification: 1 sentence explaining the score

Return JSON only:
{ "cq_scores": [ { "requirement_id": 0, "score": 2, "evidence_spans": ["...", "..."], "justification": "..." }, ... ] }`;"""

assert OLD_A in html, "Change A: CQ prompt schema not found"
html = html.replace(OLD_A, NEW_A, 1)
changes.append("annotateCQ prompt: evidence_text → evidence_spans[] + EVIDENCE RULE added")

# ── Change B: annotateCQ annotation builder ──────────────────────────────────
OLD_B = """    return llmAnnotate('cq', prompt, response, runId, data => {
      return (data.cq_scores || []).map(c => ({
        type: `cq:requirement_${c.requirement_id}`,
        text: c.evidence_text || '',
        metadata: { requirement_id: c.requirement_id, score: c.score, justification: c.justification }
      }));
    });"""

NEW_B = """    return llmAnnotate('cq', prompt, response, runId, data => {
      return (data.cq_scores || []).map(c => {
        // Backwards-compat: accept evidence_spans[] or legacy evidence_text string
        const spans = Array.isArray(c.evidence_spans) ? c.evidence_spans
                    : (c.evidence_text ? [c.evidence_text] : []);
        return {
          type: `cq:requirement_${c.requirement_id}`,
          text: spans[0] || '',
          metadata: {
            requirement_id: c.requirement_id,
            score:          c.score,
            evidence_spans: spans,
            grounded_in:    spans,    // V2 convention alias
            justification:  c.justification
          }
        };
      });
    });"""

assert OLD_B in html, "Change B: CQ annotation builder not found"
html = html.replace(OLD_B, NEW_B, 1)
changes.append("annotateCQ annotation builder: evidence_spans + grounded_in emitted; backwards-compat fallback")

# ── Change C: Verifier CQ comment update ────────────────────────────────────
OLD_C = """        // CQ with score 0 may have empty evidence_text — accept that."""
NEW_C = """        // CQ with score 0 may have empty evidence_spans — accept that."""

assert OLD_C in html, "Change C: verifier CQ comment not found"
html = html.replace(OLD_C, NEW_C, 1)
changes.append("Verifier: CQ score-0 comment updated (evidence_text → evidence_spans)")

# ── Change D: Add _normaliseArabic helper + Pass 4 CQ evidence verifier ──────
# Insert _normaliseArabic before verifyAnnotations; add Pass 4 before `return annotations;`

OLD_D1 = """  // ================================================================
  // VERIFIER — five checks. Sets verified=true|false on each annotation.
  // ================================================================
  function verifyAnnotations(annotations, response) {"""

NEW_D1 = """  // ================================================================
  // ARABIC NORMALISATION — for tolerant span matching (Tier 4J D4)
  // ================================================================
  const ARABIC_NORMALISATION_MAP = [
    [/[إأآا]/g, 'ا'],   // collapse hamza-bearing alifs to bare alif
    [/ى/g,                     'ي'],   // collapse alif maqsura to ya
    [/ة/g,                     'ه'],   // collapse taa marbuta to ha
    [/ؤ/g,                     'و'],   // collapse hamza-on-waw to waw
    [/ئ/g,                     'ي']    // collapse hamza-on-ya to ya
  ];

  function _normaliseArabic(s) {
    return ARABIC_NORMALISATION_MAP.reduce((acc, [re, sub]) => acc.replace(re, sub), s);
  }

  // ================================================================
  // VERIFIER — five checks. Sets verified=true|false on each annotation.
  // ================================================================
  function verifyAnnotations(annotations, response) {"""

assert OLD_D1 in html, "Change D1: verifyAnnotations header not found"
html = html.replace(OLD_D1, NEW_D1, 1)
changes.append("_normaliseArabic helper added before verifyAnnotations")

OLD_D2 = """    return annotations;
  }

  // ================================================================
  // RENDER — annotated text view + popover + summary + list
  // ================================================================"""

NEW_D2 = """    // Pass 4 — CQ evidence verification (Tier 4J D4).
    // For each CQ annotation, verify every evidence_span appears in response.
    // Two-tier: strict match first; normalisation-tolerant fallback if strict fails.
    // Tolerant matches count as verified for density purposes but are flagged in audit.
    {
      const normResponse = _normaliseArabic(response);
      annotations.filter(a => a.family === 'cq').forEach(ann => {
        const spans                    = ann.metadata?.evidence_spans || [];
        const unverified               = [];
        const verifiedWithNormalisation = [];
        for (const span of spans) {
          if (response.includes(span)) continue;               // strict pass
          if (normResponse.includes(_normaliseArabic(span))) { // tolerant pass
            verifiedWithNormalisation.push(span);
            continue;
          }
          unverified.push(span);                               // fail
        }
        if (unverified.length > 0)
          ann.metadata._evidence_unverified = unverified;
        if (verifiedWithNormalisation.length > 0)
          ann.metadata._evidence_verified_with_normalisation = verifiedWithNormalisation;
        ann.verification_status =
            unverified.length > 0                ? 'partial'
          : verifiedWithNormalisation.length > 0  ? 'verified_with_normalisation'
          : 'verified';
      });
    }

    return annotations;
  }

  // ================================================================
  // RENDER — annotated text view + popover + summary + list
  // ================================================================"""

assert OLD_D2 in html, "Change D2: verifyAnnotations return not found"
html = html.replace(OLD_D2, NEW_D2, 1)
changes.append("Pass 4 CQ evidence verification added to verifyAnnotations (normalisation-tolerant)")

# ── Change E: computeInterpretationObject section 2g ─────────────────────────
OLD_E = """        // ── 3. cap_directives ─────────────────────────────────────────────────
    const cap_directives = [];"""

NEW_E = """    // ── 2g. Content Quality profile (Tier 4J) ────────────────────────────────
    // D2: no-evidence enforcement — score ≥1 with no evidence_spans → force to 0.
    // D3: density caps — verified spans only (strict + tolerant-normalised, not unverified).
    // Idempotence guard: _original_score ??= prevents double-mutation on re-run.
    const SCORE_2_DENSITY_WORD_THRESHOLD = 7; // calibrated for Arabic; revisit post-batch (see D3 spec)
    const cqAnns_ie = activeAnns.filter(a => a.family === 'cq');

    // D2: no-evidence enforcement
    for (const ann of cqAnns_ie) {
      const score = ann.metadata?.score;
      const spans = ann.metadata?.evidence_spans || [];
      if (typeof score === 'number' && score > 0 && spans.length === 0) {
        ann.metadata._original_score         = ann.metadata._original_score ?? score;
        ann.metadata.score                   = 0;
        ann.metadata._forced_zero_no_evidence = true;
        ann.metadata._zero_note              = 'Forced to 0: score ≥1 with no evidence_spans';
      }
    }

    // D3: density caps on verified spans only
    for (const ann of cqAnns_ie) {
      const score = ann.metadata?.score;
      if (typeof score !== 'number' || score <= 0) continue;
      const allSpans      = ann.metadata?.evidence_spans || [];
      const unverified    = ann.metadata?._evidence_unverified || [];
      const verifiedSpans = allSpans.filter(s => !unverified.includes(s));
      const wc = s => s.trim().split(/\s+/).filter(Boolean).length;
      const longest = verifiedSpans.reduce((m, s) => Math.max(m, wc(s)), 0);
      const total   = verifiedSpans.reduce((sum, s) => sum + wc(s), 0);
      let cap = null;
      if (score === 3 && longest < 12 && total < 15) cap = 2;
      if (score === 2 && longest < SCORE_2_DENSITY_WORD_THRESHOLD) cap = 1;
      if (cap !== null && cap < score) {
        ann.metadata._original_score    = ann.metadata._original_score ?? score;
        ann.metadata.score              = cap;
        ann.metadata._capped_by_density  = true;
        ann.metadata._density_note      = `Capped ${score} → ${cap}: verified evidence too thin (longest ${longest}w, total ${total}w)`;
      }
    }

    // Build per-requirement summary
    const cqPerReq = cqAnns_ie.map(ann => ({
      requirement_id:      ann.metadata.requirement_id,
      score:               ann.metadata.score,
      original_score:      ann.metadata._original_score ?? ann.metadata.score,
      evidence_spans:      ann.metadata.evidence_spans || [],
      justification:       ann.metadata.justification,
      cap_applied:         ann.metadata._forced_zero_no_evidence ? 'no_evidence'
                         : ann.metadata._capped_by_density
                           ? `density_score_${ann.metadata._original_score}`
                           : null,
      verification_status: ann.verification_status || 'verified'
    }));

    const cqScores       = cqPerReq.map(r => r.score);
    const cqMeanScore    = cqScores.length ? cqScores.reduce((s, v) => s + v, 0) / cqScores.length : 0;
    const cqDerived      = Math.round(cqMeanScore * (100 / 3));

    const cqEnfEvents = {
      no_evidence_forced_zero:            cqAnns_ie.filter(a => a.metadata._forced_zero_no_evidence).length,
      density_capped_3_to_2:              cqAnns_ie.filter(a => a.metadata._capped_by_density && a.metadata._original_score === 3).length,
      density_capped_2_to_1:              cqAnns_ie.filter(a => a.metadata._capped_by_density && a.metadata._original_score === 2).length,
      unverified_spans_excluded:          cqAnns_ie.reduce((s, a) => s + (a.metadata._evidence_unverified?.length || 0), 0),
      verified_with_normalisation_count:  cqAnns_ie.reduce((s, a) => s + (a.metadata._evidence_verified_with_normalisation?.length || 0), 0)
    };

    const cqTotalSpans = cqPerReq.reduce((s, r) => s + r.evidence_spans.length, 0);
    const cqVerSpans   = cqTotalSpans - cqEnfEvents.unverified_spans_excluded;
    const allVerSpans  = cqPerReq.flatMap(r => {
      const unv = cqAnns_ie.find(a => a.metadata.requirement_id === r.requirement_id)
                    ?.metadata._evidence_unverified || [];
      return r.evidence_spans.filter(s => !unv.includes(s));
    });
    const _wcLen = s => s.trim().split(/\s+/).filter(Boolean).length;
    const cqLongest  = allVerSpans.reduce((m, s) => Math.max(m, _wcLen(s)), 0);
    const cqMeanSpan = allVerSpans.length
      ? Math.round(allVerSpans.reduce((s, sp) => s + _wcLen(sp), 0) / allVerSpans.length)
      : 0;

    // Reuse counts (for D5 and evidence_summary)
    const cqSpanCounts = new Map();
    for (const ann of cqAnns_ie) {
      for (const s of (ann.metadata?.evidence_spans || [])) {
        cqSpanCounts.set(s, (cqSpanCounts.get(s) || 0) + 1);
      }
    }
    const cqDupes      = [...cqSpanCounts.entries()].filter(([, n]) => n > 1);
    const cqHeavyReuse = cqDupes.filter(([, n]) => n >= 3);

    // D9 confidence
    const anyEnforcement = cqEnfEvents.no_evidence_forced_zero > 0
                        || cqEnfEvents.density_capped_3_to_2 > 0
                        || cqEnfEvents.density_capped_2_to_1 > 0;
    const anyUnverified  = cqEnfEvents.unverified_spans_excluded > 0;
    let cqConf, cqConfReason;
    if (word_count < 30) {
      cqConf = 'UNMEASURABLE'; cqConfReason = null;
    } else if (anyEnforcement) {
      cqConf = 'MEDIUM'; cqConfReason = 'enforcement_events';
    } else if (anyUnverified) {
      cqConf = 'MEDIUM'; cqConfReason = 'unverified_spans';
    } else {
      cqConf = 'HIGH'; cqConfReason = null;
    }

    dp.content_quality = Object.assign(dp.content_quality || {}, {
      per_requirement:    cqPerReq,
      mean_score:         cqMeanScore,
      derived_score:      cqDerived,
      confidence:         cqConf,
      confidence_reason:  cqConfReason,
      enforcement_events: cqEnfEvents,
      evidence_summary: {
        total_verified_spans:                cqVerSpans,
        total_unverified_spans:              cqEnfEvents.unverified_spans_excluded,
        total_verified_with_normalisation:   cqEnfEvents.verified_with_normalisation_count,
        longest_span_words:                  cqLongest,
        mean_span_words:                     cqMeanSpan,
        reused_spans_count:                  cqDupes.length,
        heavy_reused_spans_count:            cqHeavyReuse.length
      }
    });

        // ── 3. cap_directives ─────────────────────────────────────────────────
    const cap_directives = [];"""

assert OLD_E in html, "Change E: cap_directives anchor not found"
html = html.replace(OLD_E, NEW_E, 1)
changes.append("computeInterpretationObject section 2g: CQ profile with enforcement + density caps + dp.content_quality")

# ── Change F: computeScoreObject CQ branch reads derived_score from interpretObj ─
OLD_F = """    // ── Content Quality ──────────────────────────────────────
    const cqAnns = annotations.filter(a => a.family === 'cq');
    let cq_dim;
    if (cqAnns.length === 0) {
      cq_dim = 0;
    } else {
      const scores = cqAnns.map(a => (a.metadata && a.metadata.score != null) ? a.metadata.score : 0);
      const mean   = scores.reduce((s, v) => s + v, 0) / scores.length;
      cq_dim = Math.min(100, Math.round(mean * (100 / 3)));
    }"""

NEW_F = """    // ── Content Quality ──────────────────────────────────────
    // Tier 4J: reads derived_score from InterpretationObject (D7).
    // The interpretation engine ran enforcement + density caps before producing this score.
    // Legacy fallback: mean × 100/3 (used when interpretObj unavailable).
    const cqProfile = interpretObj
      && interpretObj.dimension_profiles
      && interpretObj.dimension_profiles.content_quality;
    let cq_dim;
    if (cqProfile && typeof cqProfile.derived_score === 'number') {
      cq_dim = cqProfile.derived_score;
    } else {
      // Legacy fallback — pre-Tier-4J mean × 100/3.
      const cqAnns = annotations.filter(a => a.family === 'cq');
      if (cqAnns.length === 0) {
        cq_dim = 0;
      } else {
        const scores = cqAnns.map(a => (a.metadata && a.metadata.score != null) ? a.metadata.score : 0);
        const mean   = scores.reduce((s, v) => s + v, 0) / scores.length;
        cq_dim = Math.min(100, Math.round(mean * (100 / 3)));
      }
    }"""

assert OLD_F in html, "Change F: CQ scorer branch not found"
html = html.replace(OLD_F, NEW_F, 1)
changes.append("computeScoreObject CQ branch: reads derived_score from interpretObj (D7)")

# ── Change G: computeGuardrailObject cq_evidence_reuse contradiction rule ────
OLD_G = """        // Per-dimension confidence — added v0.3 Tab 11 build."""

NEW_G = """    // Tier 4J (D5): cq_evidence_reuse — tiered: WARNING at light reuse, MODERATE + confidence drop at heavy.
    const HEAVY_REUSE_THRESHOLD = 3;   // same span across 3+ requirements → confidence drop
    const CQ_REUSE_FLAG_FLOOR   = 70;  // low-CQ responses with reuse are usually genuinely thin
    if (rules.cq_evidence_reuse !== false) {
      const _cqP = interpretObj && interpretObj.dimension_profiles && interpretObj.dimension_profiles.content_quality;
      const _cqDupes      = (_cqP && _cqP.evidence_summary && _cqP.evidence_summary.reused_spans_count)      || 0;
      const _cqHeavy      = (_cqP && _cqP.evidence_summary && _cqP.evidence_summary.heavy_reused_spans_count) || 0;
      const _cqScore      = scoreObj.dimensions.content_quality;
      if (_cqScore >= CQ_REUSE_FLAG_FLOOR && _cqDupes > 0) {
        const _cqSeverity = _cqHeavy > 0 ? 'MODERATE' : 'WARNING';
        contradictions.push({
          rule:      'cq_evidence_reuse',
          severity:  _cqSeverity,
          dimension: 'content_quality',
          message:   _cqHeavy > 0
            ? `Content Quality is ${_cqScore} (high) and ${_cqHeavy} evidence span(s) reused across 3+ requirements — score likely inflated by double-counted evidence, confidence dropped to MEDIUM.`
            : `Content Quality is ${_cqScore} (high) but evidence reused across ${_cqDupes} requirement(s). Review whether the score is double-counted.`,
          data: { reused_spans: _cqDupes, heavy_reuse_count: _cqHeavy, cq: _cqScore }
        });
        if (_cqSeverity === 'MODERATE' && _cqP) {
          _cqP.confidence        = 'MEDIUM';
          _cqP.confidence_reason = 'heavy_evidence_reuse';
        }
      }
    }

        // Per-dimension confidence — added v0.3 Tab 11 build."""

assert OLD_G in html, "Change G: per-dimension confidence anchor not found"
html = html.replace(OLD_G, NEW_G, 1)
changes.append("computeGuardrailObject: cq_evidence_reuse tiered contradiction rule (D5)")

# ── Change H: Tab 6 HTML — add cq_evidence_reuse toggle after coh_dev_flow_split ─
OLD_H = """      <div class="gr-toggle-row">
        <div>
          <div class="gr-toggle-label">Cohesive Devices / Flow split — OC</div>
          <div class="gr-toggle-desc">Cohesive Devices score and Coherence &amp; Flow score disagree by &gt;40 points — flag for teacher review (severity depends on task type)</div>
        </div>
        <label class="toggle-switch">
          <input type="checkbox" id="gr_rule_coh_dev_flow_split" checked>
          <span class="toggle-slider"></span>
        </label>
      </div>
    </div>

    <!-- Card 4: Actions -->"""

NEW_H = """      <div class="gr-toggle-row">
        <div>
          <div class="gr-toggle-label">Cohesive Devices / Flow split — OC</div>
          <div class="gr-toggle-desc">Cohesive Devices score and Coherence &amp; Flow score disagree by &gt;40 points — flag for teacher review (severity depends on task type)</div>
        </div>
        <label class="toggle-switch">
          <input type="checkbox" id="gr_rule_coh_dev_flow_split" checked>
          <span class="toggle-slider"></span>
        </label>
      </div>
      <div class="gr-toggle-row">
        <div>
          <div class="gr-toggle-label">Evidence reuse — CQ</div>
          <div class="gr-toggle-desc">Same evidence span reused across multiple requirements — WARNING at 2 requirements, MODERATE + confidence drop at 3+ requirements (only when CQ ≥ 70)</div>
        </div>
        <label class="toggle-switch">
          <input type="checkbox" id="gr_rule_cq_evidence_reuse" checked>
          <span class="toggle-slider"></span>
        </label>
      </div>
    </div>

    <!-- Card 4: Actions -->"""

assert OLD_H in html, "Change H: Tab 6 coh_dev_flow_split toggle not found"
html = html.replace(OLD_H, NEW_H, 1)
changes.append("Tab 6 HTML: gr_rule_cq_evidence_reuse toggle added after coh_dev_flow_split")

# ── Change I: GR_DEFAULTS — add cq_evidence_reuse ────────────────────────────
OLD_I1 = """      coh_dev_flow_split: true
    }
  };"""

NEW_I1 = """      coh_dev_flow_split:  true,
      cq_evidence_reuse:   true
    }
  };"""

assert OLD_I1 in html, "Change I1: GR_DEFAULTS coh_dev_flow_split not found"
html = html.replace(OLD_I1, NEW_I1, 1)
changes.append("GR_DEFAULTS: cq_evidence_reuse: true added")

# ── Change I2: _readGrConfig — add cq_evidence_reuse ─────────────────────────
OLD_I2 = """        coh_dev_flow_split:              document.getElementById('gr_rule_coh_dev_flow_split').checked
      }"""

NEW_I2 = """        coh_dev_flow_split:              document.getElementById('gr_rule_coh_dev_flow_split').checked,
        cq_evidence_reuse:               document.getElementById('gr_rule_cq_evidence_reuse').checked
      }"""

assert OLD_I2 in html, "Change I2: _readGrConfig coh_dev_flow_split line not found"
html = html.replace(OLD_I2, NEW_I2, 1)
changes.append("_readGrConfig: cq_evidence_reuse wired")

# ── Change I3: _populateGrForm — add cq_evidence_reuse ───────────────────────
OLD_I3 = """    setChk('gr_rule_coh_dev_flow_split',      r.coh_dev_flow_split);
  }"""

NEW_I3 = """    setChk('gr_rule_coh_dev_flow_split',      r.coh_dev_flow_split);
    setChk('gr_rule_cq_evidence_reuse',       r.cq_evidence_reuse);
  }"""

assert OLD_I3 in html, "Change I3: _populateGrForm coh_dev_flow_split line not found"
html = html.replace(OLD_I3, NEW_I3, 1)
changes.append("_populateGrForm: cq_evidence_reuse wired")

# ── Change J: Tab 11 CQ enforcement events ───────────────────────────────────
# After the coh_dev_flow_split indicator block, add content_quality enforcement rendering
OLD_J = """      // Tier 4H (D8a): organisation_coherence — coh_dev_flow_split indicator (teacher report only).
      if (dim === 'organisation_coherence') {
        const go_contradictions = go.contradictions || [];
        if (go_contradictions.some(c => c.rule === 'coh_dev_flow_split')) {
          if (notesHtml.startsWith('<span style="color:var(--muted)')) notesHtml = '';
          notesHtml += '<span class="tr-note-pill warning">⚠ coh.dev/flow split</span>';
        }
      }"""

NEW_J = """      // Tier 4H (D8a): organisation_coherence — coh_dev_flow_split indicator (teacher report only).
      if (dim === 'organisation_coherence') {
        const go_contradictions = go.contradictions || [];
        if (go_contradictions.some(c => c.rule === 'coh_dev_flow_split')) {
          if (notesHtml.startsWith('<span style="color:var(--muted)')) notesHtml = '';
          notesHtml += '<span class="tr-note-pill warning">⚠ coh.dev/flow split</span>';
        }
      }
      // Tier 4J: content_quality — enforcement events + normalisation footnote.
      if (dim === 'content_quality') {
        const cqDp = run.interpretation_object
          && run.interpretation_object.dimension_profiles
          && run.interpretation_object.dimension_profiles.content_quality;
        if (cqDp) {
          const ev = cqDp.enforcement_events || {};
          const enfTotal = (ev.no_evidence_forced_zero || 0)
                         + (ev.density_capped_3_to_2  || 0)
                         + (ev.density_capped_2_to_1  || 0);
          if (enfTotal > 0) {
            if (notesHtml.startsWith('<span style="color:var(--muted)')) notesHtml = '';
            notesHtml += '<span class="tr-note-pill warning" title="'
              + _esc(`No-evidence zeros: ${ev.no_evidence_forced_zero || 0}; Density 3→2: ${ev.density_capped_3_to_2 || 0}; Density 2→1: ${ev.density_capped_2_to_1 || 0}`)
              + '">⚠ ' + enfTotal + ' enforcement event' + (enfTotal > 1 ? 's' : '') + '</span>';
          }
          // Per-requirement: show struck-through original scores where enforcement fired
          if (cqDp.per_requirement && cqDp.per_requirement.some(r => r.cap_applied !== null)) {
            const reqNotes = cqDp.per_requirement
              .filter(r => r.cap_applied !== null)
              .map(r => {
                const orig = r.original_score;
                const curr = r.score;
                const tip  = r.cap_applied === 'no_evidence'
                  ? 'Forced to 0: no evidence_spans'
                  : `Capped ${orig}→${curr}: evidence too thin`;
                return `Req ${r.requirement_id}: <s>${orig}</s>→${curr} (${tip})`;
              }).join('; ');
            notesHtml += '<span class="tr-note-pill" title="' + _esc(reqNotes) + '">score corrections applied</span>';
          }
          // Normalisation footnote
          if ((ev.verified_with_normalisation_count || 0) > 0) {
            notesHtml += '<span class="tr-note-pill" style="font-size:.72rem;" title="LLM quoted evidence with hamza/alif normalisation; tolerant match accepted">hamza-norm spans: ' + ev.verified_with_normalisation_count + '</span>';
          }
          // CQ evidence reuse indicator
          const go_contradictions_cq = go.contradictions || [];
          if (go_contradictions_cq.some(c => c.rule === 'cq_evidence_reuse')) {
            const cqC = go_contradictions_cq.find(c => c.rule === 'cq_evidence_reuse');
            if (notesHtml.startsWith('<span style="color:var(--muted)')) notesHtml = '';
            notesHtml += '<span class="tr-note-pill ' + (cqC.severity === 'MODERATE' ? 'warning' : '') + '">⚠ evidence reuse</span>';
          }
        }
      }"""

assert OLD_J in html, "Change J: Tab 11 coh_dev_flow_split indicator block not found"
html = html.replace(OLD_J, NEW_J, 1)
changes.append("Tab 11: CQ enforcement events + normalisation footnote + evidence reuse indicator")

# ── Acceptance tests (inline, non-mutating) ───────────────────────────────────
# These exercise the logic that will run in-browser. We test the Python equivalents.

def _normalise_arabic(s):
    import re
    s = re.sub(r'[إأآا]', 'ا', s)
    s = re.sub(r'ى',      'ي', s)
    s = re.sub(r'ة',      'ه', s)
    s = re.sub(r'ؤ',      'و', s)
    s = re.sub(r'ئ',      'ي', s)
    return s

def _make_ann(score, spans):
    return {'metadata': {'score': score, 'evidence_spans': spans}, 'family': 'cq', 'verification_status': 'verified'}

def _enforce_no_evidence(anns):
    for ann in anns:
        score = ann['metadata'].get('score')
        spans = ann['metadata'].get('evidence_spans', [])
        if isinstance(score, (int, float)) and score > 0 and len(spans) == 0:
            ann['metadata'].setdefault('_original_score', score)
            ann['metadata']['score'] = 0
            ann['metadata']['_forced_zero_no_evidence'] = True

def _apply_density_caps(anns, threshold=7):
    for ann in anns:
        score = ann['metadata'].get('score')
        if not isinstance(score, (int, float)) or score <= 0:
            continue
        all_spans = ann['metadata'].get('evidence_spans', [])
        unverified = ann['metadata'].get('_evidence_unverified', [])
        verified   = [s for s in all_spans if s not in unverified]
        wc = lambda s: len(s.strip().split())
        longest = max((wc(s) for s in verified), default=0)
        total   = sum(wc(s) for s in verified)
        cap = None
        if score == 3 and longest < 12 and total < 15:
            cap = 2
        if score == 2 and longest < threshold:
            cap = 1
        if cap is not None and cap < score:
            ann['metadata'].setdefault('_original_score', score)
            ann['metadata']['score'] = cap
            ann['metadata']['_capped_by_density'] = True

# AC1: normalisation — الى → strict fails, tolerant passes
response_ac1   = 'ذهبت الى المدرسة'
span_ac1       = 'إلى المدرسة'
strict_pass    = span_ac1 in response_ac1
tolerant_pass  = _normalise_arabic(span_ac1) in _normalise_arabic(response_ac1)
assert not strict_pass,   "AC1a: strict should fail"
assert tolerant_pass,     "AC1b: tolerant should pass"

# AC2: normalisation — no match even after normalisation
span_ac2 = 'من الحقل البعيد'
assert not (_normalise_arabic(span_ac2) in _normalise_arabic(response_ac1)), "AC2: should not match"

# AC3: no-evidence enforcement
ann3 = _make_ann(3, [])
_enforce_no_evidence([ann3])
assert ann3['metadata']['score'] == 0,                         "AC3a: forced to 0"
assert ann3['metadata']['_forced_zero_no_evidence'],           "AC3b: flag set"
assert ann3['metadata']['_original_score'] == 3,              "AC3c: original preserved"

# AC4: density cap 3→2 (4-word span)
ann4 = _make_ann(3, ['ذهبت إلى هناك'])  # 3 words
_apply_density_caps([ann4])
assert ann4['metadata']['score'] == 2,              "AC4: score 3 → 2"
assert ann4['metadata']['_capped_by_density'],      "AC4: flag set"

# AC5: density cap 2→1 (6-word span, threshold=7)
ann5 = _make_ann(2, ['ذهبت إلى المدينة يوم الأحد'])  # 5 Arabic words
_apply_density_caps([ann5])
assert ann5['metadata']['score'] == 1,   "AC5: score 2 → 1 (6 words < 7)"

# AC6: 7-word span should NOT be capped
ann6 = _make_ann(2, ['ذهبت إلى المدينة الجميلة يوم الأحد الماضي'])  # 7 words
_apply_density_caps([ann6])
assert ann6['metadata']['score'] == 2,   "AC6: 7-word span not capped"

# AC7: idempotence — _original_score guard
ann7 = _make_ann(3, [])
_enforce_no_evidence([ann7])
_enforce_no_evidence([ann7])  # second run
assert ann7['metadata']['_original_score'] == 3,   "AC7: original_score not overwritten"
assert ann7['metadata']['score'] == 0,             "AC7: score still 0"

# AC8: reuse counting basics
spans_reuse = ['span A', 'span B', 'span A', 'span A']
from collections import Counter
counts = Counter(spans_reuse)
dupes = {s: n for s, n in counts.items() if n > 1}
heavy = {s: n for s, n in dupes.items() if n >= 3}
assert len(dupes) == 1,         "AC8: one duplicate span"
assert len(heavy) == 1,         "AC8: one heavy-reuse span"

print("All acceptance tests passed.")

# ── Write out ─────────────────────────────────────────────────────────────────
with open(SRC, 'w', encoding='utf-8') as f:
    f.write(html)

final_len = html.count('\n') + 1
print(f"Read: {original_len} lines")
for i, c in enumerate(changes, 1):
    print(f"Change {i}: {c}.")
print(f"Written: {final_len} lines ({final_len - original_len:+d})")
print("Done.")
