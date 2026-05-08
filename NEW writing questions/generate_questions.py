"""
Auto-generate task requirements + development markers + rewritten stem
for pending questions in the new_question_bank.csv.

Usage:
  set OPENAI_API_KEY=sk-...
  python generate_questions.py --limit 5
  python generate_questions.py --refs W-B2-3,W-B2-6
  python generate_questions.py            (processes all pending)

Reads:  output/new_question_bank.csv
Writes: output/new_question_bank.csv (updated rows)
Saves backup before writing.
"""

import argparse
import csv
import json
import os
import shutil
import sys
import time
from pathlib import Path

import openai

BASE = Path(__file__).parent
CSV_PATH = BASE / "output" / "new_question_bank.csv"
PROMPTS_DIR = BASE / "prompts"

# Word range presets per CEFR
WORD_RANGES = {
    'a1': (25, 80), 'a2': (40, 120), 'b1': (50, 300),
    'b2': (100, 400), 'c1': (150, 500), 'c2': (150, 500),
}

MODEL = "gpt-4o"

def load_prompt(name):
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")

def call_openai(prompt, system="You are an expert assessment author. Always return valid JSON only — no prose, no markdown fences.", max_tokens=2000):
    client = openai.OpenAI()
    res = client.chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )
    text = res.choices[0].message.content
    # extract JSON
    import re
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError("no JSON in response: " + text[:200])
    return json.loads(m.group(0))

def fill(template, **kwargs):
    out = template
    for k, v in kwargs.items():
        out = out.replace("{" + k + "}", str(v))
    return out

def process_question(row, prompts):
    cefr = row['cefr_level'].lower()
    task_type = row['task_type'].lower()
    topic = row['topic'] or "general"
    original_stem = row.get('question_prompt') or row.get('original_question') or ""
    # NB: in our CSV the original question comes from the source file. We need to read it from input/old_questions.csv.
    # Easiest: pass original stem in via the script harness.

    # 1. Generate task requirements from the original stem
    p1 = fill(prompts['task_reqs'],
              QUESTION_STEM=original_stem,
              CEFR_LEVEL=cefr,
              TASK_TYPE=task_type,
              TOPIC=topic)
    r1 = call_openai(p1)
    task_requirements = r1.get('task_requirements', [])
    if len(task_requirements) != 3:
        raise ValueError(f"expected 3 task_requirements, got {len(task_requirements)}")

    # 2. Generate development markers from those task requirements
    p2 = fill(prompts['markers'],
              TASK_REQUIREMENTS=json.dumps(task_requirements, indent=2),
              QUESTION_STEM=original_stem,
              CEFR_LEVEL=cefr,
              TOPIC=topic)
    r2 = call_openai(p2, max_tokens=3000)
    markers = r2.get('development_markers', [])
    if len(markers) != 4:
        raise ValueError(f"expected 4 markers, got {len(markers)}")

    # 3. Rewrite the question stem with the 3 bullets
    p3 = fill(prompts['stem'],
              ORIGINAL_STEM=original_stem,
              TASK_REQUIREMENTS=json.dumps(task_requirements),
              CEFR_LEVEL=cefr,
              TASK_TYPE=task_type,
              TOPIC=topic)
    r3 = call_openai(p3)
    new_stem = r3.get('question_stem', '')
    if not new_stem:
        raise ValueError("empty rewritten stem")

    return {
        'new_stem': new_stem,
        'task_requirements': task_requirements,
        'development_markers': markers,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None, help='only process first N pending rows')
    parser.add_argument('--refs', type=str, default=None, help='comma-separated list of refs to process')
    parser.add_argument('--cefr', type=str, default=None, help='only process rows of this CEFR level')
    parser.add_argument('--force', action='store_true', help='re-process even rows already marked auto-generated/verified')
    args = parser.parse_args()

    if 'OPENAI_API_KEY' not in os.environ:
        print("ERROR: OPENAI_API_KEY environment variable not set.")
        print("Run:  set OPENAI_API_KEY=sk-...your-key...")
        sys.exit(1)

    # Backup CSV
    backup = CSV_PATH.with_suffix(f".backup-{int(time.time())}.csv")
    shutil.copy(CSV_PATH, backup)
    print(f"Backup saved: {backup.name}")

    # Load prompts
    prompts = {
        'task_reqs': load_prompt('generate_task_requirements.md'),
        'markers':   load_prompt('generate_quality_markers.md'),
        'stem':      load_prompt('rewrite_question_stem.md'),
    }

    # Load original questions to get the source stems
    old_path = BASE / "input" / "old_questions.csv"
    with open(old_path, 'r', encoding='utf-8') as fh:
        old_rows = {r['ref_#']: r for r in csv.DictReader(fh)}

    # Load new bank
    with open(CSV_PATH, 'r', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Filter pending (or all rows if --force)
    if args.force:
        pending = list(rows)
    else:
        pending = [r for r in rows if r['status'] == 'pending']
    if args.refs:
        wanted = set(args.refs.split(','))
        pending = [r for r in pending if r['ref_#'] in wanted]
    if args.cefr:
        pending = [r for r in pending if r['cefr_level'].lower() == args.cefr.lower()]
    if args.limit:
        pending = pending[:args.limit]

    print(f"Processing {len(pending)} pending row(s)")

    success = 0
    failed = 0
    for i, row in enumerate(pending, 1):
        ref = row['ref_#']
        old = old_rows.get(ref, {})
        original_stem = (old.get('question') or '').strip()
        if not original_stem:
            print(f"[{i}/{len(pending)}] {ref}: no original question text — SKIPPING")
            row['status'] = 'failed'
            row['notes'] = 'no original question text in input'
            failed += 1
            continue

        # Inject the original stem so process_question can read it
        row['_original_stem'] = original_stem
        # Also fill word_range default if missing
        if not row['word_count_min'] or not row['word_count_max']:
            cefr = row['cefr_level'].lower()
            if cefr in WORD_RANGES:
                row['word_count_min'], row['word_count_max'] = WORD_RANGES[cefr]

        try:
            print(f"[{i}/{len(pending)}] {ref} ({row['cefr_level']} · {row['task_type']})... ", end="", flush=True)
            row_for_processing = dict(row)
            row_for_processing['question_prompt'] = original_stem  # the source for this round
            result = process_question(row_for_processing, prompts)

            row['question_prompt'] = result['new_stem']
            for j in range(3):
                m = result['development_markers'][j]
                row[f'requirement_{j+1}'] = m.get('requirement', '')
                row[f'req_{j+1}_score_0'] = 'absent'
                row[f'req_{j+1}_score_1'] = m.get('1_mentioned', '')
                row[f'req_{j+1}_score_2'] = m.get('2_developed', '')
                row[f'req_{j+1}_score_3'] = m.get('3_extended', '')
            # 4th marker stays as-is (verbatim generic, already filled)
            row['status'] = 'auto-generated'
            row['notes'] = ''
            success += 1
            print("OK")
        except Exception as e:
            row['status'] = 'failed'
            row['notes'] = f"error: {str(e)[:150]}"
            failed += 1
            print(f"FAILED: {e}")

        # Save after each row (incremental)
        with open(CSV_PATH, 'w', encoding='utf-8', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=fieldnames)
            w.writeheader()
            for r in rows:
                # strip helper field
                r_clean = {k: v for k, v in r.items() if not k.startswith('_')}
                w.writerow(r_clean)

    print(f"\nDone. Success: {success}, Failed: {failed}")

if __name__ == "__main__":
    main()
