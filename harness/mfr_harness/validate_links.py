"""Check a Layer 1 link file (JSONL, OLD_AGENT_IMPROVEMENTS.md) or a Layer 0 CSV (url,url_type).

L1 checks: every line parses and matches schema/link_record.schema.json; every link's found_on is a page
record's url in the same file; urls are normalised (no fragment, no whitespace); one page record per url.
L0 checks: header is url,url_type; every row has an absolute http(s) url.

Usage:
    python -m mfr_harness.validate_links <file.jsonl|file.csv>
Exit code 1 if any ERROR is found.
"""
import argparse
import csv
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

from .config import HARNESS_ROOT, load_json

LINK_SCHEMA_PATH = HARNESS_ROOT / 'schema' / 'link_record.schema.json'
L1_URL_TYPES = {'page', 'pdf', 'image', 'cad', 'bim', 'archive', 'spreadsheet', 'video', 'other'}


def _url_problem(u):
    if not isinstance(u, str) or not u.startswith(('http://', 'https://')):
        return 'not an absolute http(s) url'
    if any(c.isspace() for c in u):
        return 'contains whitespace (not normalised)'
    if urlsplit(u).fragment:
        return 'has a #fragment (not normalised)'
    return None


def validate_l1_lines(lines):
    """lines: iterable of JSON strings. Returns (errors, warnings, counts)."""
    import jsonschema
    validator = jsonschema.Draft202012Validator(load_json(LINK_SCHEMA_PATH))
    errors, warnings = [], []
    pages, links = {}, []
    for n, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f'line {n}: not JSON: {e}')
            continue
        errs = sorted(validator.iter_errors(rec), key=lambda e: list(e.absolute_path))
        if errs:
            errors.append(f'line {n}: schema: {errs[0].message}')
            continue
        for key in ('url', 'found_on', 'final_url', 'canonical_url'):
            if rec.get(key):
                p = _url_problem(rec[key])
                if p:
                    errors.append(f'line {n}: {key} {p}: {rec[key]}')
        if rec['record'] == 'page':
            if rec['url'] in pages:
                errors.append(f'line {n}: duplicate page record for {rec["url"]} (first on line {pages[rec["url"]]})')
            pages[rec['url']] = n
            if rec.get('status') == 200 and not rec.get('html_snapshot'):
                warnings.append(f'line {n}: page without html_snapshot; processing will fetch it once')
        else:
            links.append((n, rec))
    for n, rec in links:
        if rec['found_on'] is None:
            warnings.append(f'line {n}: link with no found_on (inventory-only entry): {rec["url"]}')
        elif rec['found_on'] not in pages:
            errors.append(f'line {n}: found_on has no page record in this file: {rec["found_on"]}')
    return errors, warnings, {'pages': len(pages), 'links': len(links)}


def validate_l0_rows(path):
    errors = []
    with open(path, newline='') as f:
        r = csv.reader(f)
        header = next(r, None)
        if header != ['url', 'url_type']:
            errors.append(f'header must be url,url_type (got {header})')
        n = 0
        for i, row in enumerate(r, 2):
            n += 1
            if not row or not row[0].strip().startswith(('http://', 'https://')):
                errors.append(f'row {i}: not an absolute http(s) url: {row[:1]}')
    return errors, [], {'rows': n}


def validate_file(path):
    path = Path(path)
    if path.suffix.lower() == '.csv':
        return validate_l0_rows(path)
    with open(path) as f:
        return validate_l1_lines(f)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('file')
    ap.add_argument('--max', type=int, default=30, help='print at most N messages per severity')
    args = ap.parse_args(argv)
    errors, warnings, counts = validate_file(args.file)
    for e in errors[:args.max]:
        print('ERROR', e)
    for w in warnings[:args.max]:
        print('WARN ', w)
    print(f'{args.file}: {counts}; {len(errors)} errors, {len(warnings)} warnings')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
