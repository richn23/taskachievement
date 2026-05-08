"""
Audit the generated question bank for quality issues.

Runs automated checks on each auto-generated/verified row and flags problems.

Usage:
  python audit_questions.py                    (audit everything)
  python audit_questions.py --cefr b2          (only B2)
  python audit_questions.py --refs W-B2-3      (specific refs)
  python audit_questions.py --status auto-generated   (only one status)

Outputs:
  output/audit_report.md      (human-readable report)
  output/audit_summary.csv    (one row per question with issue counts)
"""

import argparse
import csv
import re
import sys
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent
CSV_PATH = BASE / "output" / "new_question_bank.csv"

# Verbatim 4th marker
VERBATIM_4TH = {
    "score_0": "no semantically distinct extra on-topic point, OR the 'extra' content paraphrases an idea already credited under another requirement",
    "score_1": "introduces a DISTINCT extra on-topic point — not a rephrasing or repeat of any other requirement — within the question's subject, with no further detail",
    "score_2": "introduces a distinct extra on-topic point AND develops it meaningfully (a real reason, cause, or effect — not just length)",
    "score_3": "introduces a distinct extra on-topic point AND develops it AND supports it with a concrete specific that genuinely advances the argument",
}

# Vague words that suggest lack of construct precision
VAGUE_REQ_WORDS = ['aspects', 'things', 'stuff', 'lots', 'various']

# Knowledge-test red flags in requirements
KNOWLEDGE_FLAGS = ['recent news', 'famous', 'historical event', 'current event', 'named institution']

# Words that indicate "materially develops" intent
MATERIAL_LANGUAGE = ['materially develop', 'materially advance', 'genuinely advance']

# Anti-example markers
ANTIEX_LANGUAGE = ['do NOT count', 'does NOT count', 'do NOT satisfy', 'does NOT satisfy']

# Boundary example markers
BOUNDARY_LANGUAGE = ['scores 2, not 3', 'scores 2 not 3']


def audit_row(row):
    """Return a list of (severity, issue) tuples for one row."""
    issues = []
    cefr = row.get('cefr_level', '').lower()

    # Skip rows that aren't yet processed
    if row.get('status', '') not in ('auto-generated', 'verified'):
        return issues

    # ---------- Question prompt checks ----------
    qp = row.get('question_prompt', '') or ''
    if not qp.strip():
        issues.append(('ERROR', 'Empty question_prompt'))
    else:
        bullets = re.findall(r'^\s*-\s+\S', qp, flags=re.MULTILINE)
        if len(bullets) != 3:
            issues.append(('WARN', f'Expected 3 bullets in stem, found {len(bullets)}'))

    # ---------- Per-requirement checks ----------
    for i in range(1, 4):
        req = (row.get(f'requirement_{i}', '') or '').strip()
        if not req:
            issues.append(('ERROR', f'Req {i}: missing requirement label'))
            continue

        # Construct precision: flag vague words
        for vague in VAGUE_REQ_WORDS:
            if vague in req.lower():
                issues.append(('WARN', f'Req {i}: contains vague word "{vague}" — may lack construct precision'))

        # Knowledge test
        for kw in KNOWLEDGE_FLAGS:
            if kw in req.lower():
                issues.append(('WARN', f'Req {i}: contains knowledge-anchor "{kw}" — student may need real-world facts'))

        # Score descriptors
        s2 = (row.get(f'req_{i}_score_2', '') or '').strip()
        s3 = (row.get(f'req_{i}_score_3', '') or '').strip()

        if not s2:
            issues.append(('ERROR', f'Req {i}: missing rung-2 descriptor'))
        else:
            # Boundary example check
            has_boundary = any(b in s2.lower() for b in BOUNDARY_LANGUAGE)
            if not has_boundary:
                issues.append(('INFO', f'Req {i}: rung-2 missing "scores 2, not 3" boundary example'))

        if not s3:
            issues.append(('ERROR', f'Req {i}: missing rung-3 descriptor'))
        else:
            # Material develops language
            has_material = any(m in s3.lower() for m in MATERIAL_LANGUAGE)
            if not has_material:
                issues.append(('WARN', f'Req {i}: rung-3 missing "materially develop" language'))

            # Anti-example
            has_antiex = any(a in s3 for a in ANTIEX_LANGUAGE)
            if not has_antiex:
                issues.append(('WARN', f'Req {i}: rung-3 missing "do NOT count" anti-example'))

            # NAMED in caps (forbidden)
            if re.search(r'\bNAMED\b', s3):
                issues.append(('ERROR', f'Req {i}: rung-3 uses literal NAMED in capitals (forbidden)'))

            # B2/C1 should ideally use "TWO" or comparison/contrast/qualification
            if cefr in ('b2', 'c1', 'c2'):
                has_two = bool(re.search(r'\bTWO\b', s3))
                has_compare = bool(re.search(r'compar|contrast|categori|qualif|trade-off|counter-evidence', s3.lower()))
                if not (has_two or has_compare):
                    issues.append(('INFO', f'Req {i}: B2+ rung-3 lacks TWO specifics OR comparison/contrast/qualification — may be B1-style'))

    # ---------- 4th generic marker check ----------
    for k, v in VERBATIM_4TH.items():
        actual = (row.get(f'req_4_{k}', '') or '').strip()
        # Allow trailing/leading whitespace
        if actual != v.strip():
            # Also check after normalising em-dashes
            if actual.replace('—', '-') != v.strip().replace('—', '-'):
                issues.append(('ERROR', f'4th marker: {k} drifted from verbatim text'))

    # ---------- Duplicate descriptors check ----------
    for i in range(1, 4):
        s1 = row.get(f'req_{i}_score_1', '') or ''
        s2 = row.get(f'req_{i}_score_2', '') or ''
        s3 = row.get(f'req_{i}_score_3', '') or ''
        if s1 and s1 == s2:
            issues.append(('ERROR', f'Req {i}: rung 1 identical to rung 2'))
        if s2 and s2 == s3:
            issues.append(('ERROR', f'Req {i}: rung 2 identical to rung 3'))

    return issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cefr', type=str, default=None)
    parser.add_argument('--refs', type=str, default=None)
    parser.add_argument('--status', type=str, default=None,
                        help='filter by status (auto-generated, verified, etc.)')
    args = parser.parse_args()

    with open(CSV_PATH, 'r', encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))

    # Filter
    if args.cefr:
        rows = [r for r in rows if r['cefr_level'].lower() == args.cefr.lower()]
    if args.refs:
        wanted = set(args.refs.split(','))
        rows = [r for r in rows if r['ref_#'] in wanted]
    if args.status:
        rows = [r for r in rows if r['status'] == args.status]

    # Audit
    report_lines = ['# Audit report', '']
    summary_rows = []
    severity_counts = defaultdict(int)
    issue_counts = defaultdict(int)

    audited = 0
    clean = 0
    for r in rows:
        if r['status'] not in ('auto-generated', 'verified'):
            continue
        audited += 1
        issues = audit_row(r)
        ref = r['ref_#']
        cefr = r['cefr_level']
        status = r['status']

        sev_counts = defaultdict(int)
        for sev, _ in issues:
            sev_counts[sev] += 1
            severity_counts[sev] += 1

        if not issues:
            clean += 1
            continue

        report_lines.append(f'## {ref} ({cefr.upper()} · {status})')
        report_lines.append('')
        for sev, msg in issues:
            report_lines.append(f'- **{sev}**: {msg}')
            issue_counts[msg] += 1
        report_lines.append('')

        summary_rows.append({
            'ref': ref,
            'cefr': cefr,
            'status': status,
            'errors': sev_counts['ERROR'],
            'warnings': sev_counts['WARN'],
            'info': sev_counts['INFO'],
            'total_issues': len(issues),
        })

    # Header summary
    header = [
        f'**Audited**: {audited} rows',
        f'**Clean**: {clean}',
        f'**With issues**: {audited - clean}',
        f'**Errors**: {severity_counts["ERROR"]}',
        f'**Warnings**: {severity_counts["WARN"]}',
        f'**Info**: {severity_counts["INFO"]}',
        '',
        '## Most common issues',
        '',
    ]
    top_issues = sorted(issue_counts.items(), key=lambda kv: -kv[1])[:15]
    for msg, n in top_issues:
        header.append(f'- {n}× {msg}')
    header.append('')

    report = '\n'.join(header) + '\n'.join(report_lines)
    out_md = BASE / 'output' / 'audit_report.md'
    out_md.write_text(report, encoding='utf-8')

    # Summary CSV
    out_csv = BASE / 'output' / 'audit_summary.csv'
    with open(out_csv, 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['ref','cefr','status','errors','warnings','info','total_issues'])
        w.writeheader()
        w.writerows(summary_rows)

    print(f'Audited: {audited} | Clean: {clean} | With issues: {audited - clean}')
    print(f'Errors: {severity_counts["ERROR"]} | Warnings: {severity_counts["WARN"]} | Info: {severity_counts["INFO"]}')
    print(f'\nReport:  {out_md}')
    print(f'Summary: {out_csv}')


if __name__ == '__main__':
    main()
