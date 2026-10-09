"""Check a SiteRun JSON (prediction or gold) against the schema and the spec v1 quality rules.

Offline only: it never fetches URLs. Network-derived facts (http_status, mime_verified,
width/height, phash, snapshot hashes) must already be recorded in the file. Quote checks read
extracted text from <evidence>/text/<sha256>.txt.

Usage:
    python -m mfr_harness.validate runs/bray.json --site bray [--evidence runs/bray.evidence]
    python -m mfr_harness.validate gold/bray.json --site bray --gold   # evidence defaults to gold/bray.evidence
Exit code 1 if any ERROR is found.
"""
import argparse
import itertools
import re
import sys
from pathlib import Path

from . import normalize as N
from .config import SCHEMA_PATH, PRIMARY_DOC_TYPES, load_json, site_hosts

MIN_IMAGE_SIDE = 300
PHASH_DUP_DISTANCE = 6
SITEMAP_GAP = 0.15
SPEC_SHEET_TYPES = {'spec_sheet', 'submittal'}


class Report:
    def __init__(self):
        self.items = []

    def add(self, severity, where, msg):
        self.items.append((severity, where, msg))

    def count(self, severity):
        return sum(1 for s, _, _ in self.items if s == severity)


class Evidence:
    """Extracted text of cited sources, keyed by sha256 of the PDF file / page HTML."""

    def __init__(self, root):
        self.root = Path(root) / 'text' if root else None
        self._cache = {}

    @property
    def enabled(self):
        return self.root is not None and self.root.is_dir()

    def text(self, sha):
        if not self.enabled or not sha:
            return None
        if sha not in self._cache:
            p = self.root / f'{sha}.txt'
            self._cache[sha] = norm_text(p.read_text(errors='replace')) if p.is_file() else None
        return self._cache[sha]


def norm_text(s):
    s = s.replace('­', '').replace('″', '"').replace('“', '"').replace('”', '"')
    s = s.replace('’', "'").replace('–', '-').replace('—', '-').replace(' ', ' ')
    return re.sub(r'\s+', ' ', s).strip().lower()


def schema_check(run, rep):
    try:
        import jsonschema
    except ImportError:
        rep.add('WARN', 'schema', 'jsonschema not installed; schema validation skipped (pip install jsonschema)')
        return
    validator = jsonschema.Draft202012Validator(load_json(SCHEMA_PATH))
    for err in sorted(validator.iter_errors(run), key=lambda e: list(e.absolute_path)):
        path = '/'.join(str(p) for p in err.absolute_path) or '(root)'
        rep.add('ERROR', f'schema:{path}', err.message)


def _check_url(url, where, allowed, viewer_hosts, rep, allow_viewer=False):
    hosts = allowed + (viewer_hosts if allow_viewer else [])
    if not N.host_allowed(url, hosts):
        rep.add('ERROR', where, f'host not in allowlist: {url}')
    loc = N.locale_of_url(url)
    if not N.is_english(loc):
        rep.add('ERROR', where, f'non-English locale "{loc}": {url}')


class FamilyContext:
    def __init__(self, fam):
        self.fam = fam
        self.fid = fam.get('family_id', '?')
        self.page_keys = {N.match_key(fam['canonical_url'])}
        self.page_keys |= {N.match_key(a['url']) for a in fam.get('alternates', [])}
        self.page_keys |= {N.match_key(v['page_url']) for v in fam.get('variants', []) if v.get('page_url')}
        self.docs = {N.match_key(d['url'], drop_asset_params=True): d for d in fam.get('documents', [])}

    def doc_for(self, url):
        return self.docs.get(N.match_key(url, drop_asset_params=True))


def _check_one_source(src, where, ctx, rep, is_gold, ev, require_quote):
    if not src.get('url'):
        rep.add('ERROR', where, 'missing source citation')
        return
    strict = 'ERROR' if is_gold else 'WARN'
    if src.get('type') == 'pdf':
        if not src.get('page'):
            rep.add('WARN', where, 'PDF source without page number')
        doc = ctx.doc_for(src['url'])
        if doc is None:
            rep.add('ERROR', where, f'cited PDF is not in the family documents: {src["url"]}')
        else:
            if doc.get('sha256') and src.get('snapshot_sha256') and doc['sha256'] != src['snapshot_sha256']:
                rep.add('ERROR', where, 'snapshot_sha256 differs from the document sha256')
    if require_quote and not src.get('quote'):
        rep.add(strict, where, 'source has no verbatim quote')
    if src.get('quote'):
        sha = src.get('snapshot_sha256') or ((ctx.doc_for(src['url']) or {}).get('sha256') if src.get('type') == 'pdf' else None)
        if not sha:
            rep.add(strict, where, 'quote cannot be checked: no snapshot_sha256')
        elif ev.enabled:
            text = ev.text(sha)
            if text is None:
                rep.add(strict, where, f'no evidence text for snapshot {sha[:12]}…')
            elif norm_text(src['quote']) not in text:
                rep.add('ERROR', where, f'quote not found in source text: "{src["quote"][:60]}"')


def _sources_of(spec):
    out = list(spec.get('sources') or [])
    for alt in spec.get('alt_values') or []:
        out += alt.get('sources') or []
    return out


def _check_spec(spec, where, ctx, rep, is_gold, ev):
    srcs = spec.get('sources') or []
    if not srcs:
        rep.add('ERROR', where, 'missing source citation')
        return
    for i, s in enumerate(srcs):
        _check_one_source(s, f'{where}.sources[{i}]', ctx, rep, is_gold, ev, require_quote=True)
    for ai, alt in enumerate(spec.get('alt_values') or []):
        for i, s in enumerate(alt.get('sources') or []):
            _check_one_source(s, f'{where}.alt_values[{ai}].sources[{i}]', ctx, rep, is_gold, ev, require_quote=True)

    def is_sheet(s):
        return s.get('type') == 'pdf' and (ctx.doc_for(s['url']) or {}).get('doc_type') in SPEC_SHEET_TYPES

    every = _sources_of(spec)
    has_pdf = any(s.get('type') == 'pdf' for s in every)
    has_page = any(s.get('type') == 'page' for s in every)
    cc = spec.get('cross_check')

    # Precedence: spec sheet / submittal PDF > web page > other PDF.
    if any(is_sheet(s) for s in every):
        if not any(is_sheet(s) for s in srcs) or spec.get('display_source') != 'pdf':
            rep.add('ERROR', where, 'a spec sheet states this field, so its value must be the displayed value')
    elif has_page and spec.get('display_source') != 'page':
        rep.add('ERROR', where, 'no spec sheet states this field, so the web page value must be displayed')

    if cc == 'not_checked':
        rep.add('ERROR' if is_gold else 'WARN', where, 'cross_check not done (page and PDF must both be checked)')
    elif has_pdf and has_page:
        if cc not in ('agree', 'conflict'):
            rep.add('ERROR', where, f'page and PDF both cited but cross_check={cc}')
    elif has_pdf and cc != 'pdf_only':
        rep.add('ERROR', where, f'only PDF sources but cross_check={cc}')
    elif has_page and cc != 'page_only':
        rep.add('ERROR', where, f'only page sources but cross_check={cc}')
    if cc == 'conflict' and not spec.get('alt_values'):
        rep.add('ERROR', where, 'cross_check=conflict but alt_values is empty')
    if cc != 'conflict' and spec.get('alt_values'):
        rep.add('ERROR', where, f'alt_values present but cross_check={cc}')


def _check_pdf_provenance(ctx, rep, ev):
    """Every PDF cited for specs must be linked from one of the family's own pages and name the series."""
    cited = set()
    for k, spec in (ctx.fam.get('specs') or {}).items():
        cited |= {N.match_key(s['url'], drop_asset_params=True) for s in _sources_of(spec) if s.get('type') == 'pdf' and s.get('url')}
    for var in ctx.fam.get('variants', []):
        for spec in (var.get('spec_overrides') or {}).values():
            cited |= {N.match_key(s['url'], drop_asset_params=True) for s in _sources_of(spec) if s.get('type') == 'pdf' and s.get('url')}
    series = ctx.fam.get('series_code')
    for key in cited:
        doc = ctx.docs.get(key)
        if doc is None:
            continue  # reported by _check_one_source
        where = f'{ctx.fid}:provenance:{doc["url"]}'
        if not doc.get('found_on') or N.match_key(doc['found_on']) not in ctx.page_keys:
            rep.add('ERROR', where, 'spec PDF is not linked from one of this family\'s pages (found_on)')
        text = ev.text(doc.get('sha256'))
        if text is not None:
            needles = [n for n in (series, ctx.fam.get('name')) if n]
            if needles and not any(norm_text(n) in text or norm_text(n).replace(' ', '') in text.replace(' ', '') for n in needles):
                rep.add('WARN', where, f'PDF text does not mention series "{series}" or the family name')


def _summary_of(fam):
    kinds = {s.get('type') for spec in (fam.get('specs') or {}).values() for s in _sources_of(spec)}
    return 'both' if kinds >= {'pdf', 'page'} else 'pdf' if 'pdf' in kinds else 'page' if 'page' in kinds else 'none'


def check_family(fam, allowed, viewer_hosts, rep, is_gold, ev):
    ctx = FamilyContext(fam)
    fid = ctx.fid
    _check_url(fam['canonical_url'], f'{fid}:canonical_url', allowed, viewer_hosts, rep)
    loc = N.locale_of_url(fam['canonical_url'])
    expected_flag = N.market_flag(loc)
    if fam.get('market_flag') and expected_flag and fam['market_flag'] != expected_flag:
        rep.add('WARN', f'{fid}:market_flag', f'is {fam["market_flag"]}, URL locale "{loc}" suggests {expected_flag}')

    for i, d in enumerate(fam.get('documents', [])):
        w = f'{fid}:documents[{i}]'
        _check_url(d['url'], w, allowed, viewer_hosts, rep)
        lang = d.get('lang') or ''
        if not lang.split('+')[0].startswith('en'):
            rep.add('ERROR', w, f'document lang "{lang}" is not English-primary')
        expected_pri = 'primary' if d.get('doc_type') in PRIMARY_DOC_TYPES else 'secondary'
        if d.get('priority') and d['priority'] != expected_pri:
            rep.add('ERROR', w, f'priority {d["priority"]} inconsistent with doc_type {d.get("doc_type")}')
        if d.get('http_status') not in (200, None):
            rep.add('ERROR', w, f'http_status {d["http_status"]}')
        if d.get('http_status') is None:
            rep.add('ERROR' if is_gold else 'WARN', w, 'http_status not recorded')
        if d.get('mime_verified') is not True:
            rep.add('ERROR' if is_gold else 'WARN', w, 'file type not verified from magic bytes')
        if is_gold and not d.get('sha256'):
            rep.add('ERROR', w, 'gold document missing sha256')

    for i, c in enumerate(fam.get('cad', [])):
        w = f'{fid}:cad[{i}]'
        _check_url(c['url'], w, allowed, viewer_hosts, rep, allow_viewer=True)
        if c.get('cad_type') != 'cad_viewer' and not c.get('formats'):
            rep.add('WARN', w, 'cad file without formats[]')

    imgs = fam.get('images', [])
    for i, im in enumerate(imgs):
        w = f'{fid}:images[{i}]'
        _check_url(im['url'], w, allowed, viewer_hosts, rep)
        wd, ht = im.get('width'), im.get('height')
        if wd and ht and min(wd, ht) < MIN_IMAGE_SIDE:
            rep.add('ERROR', w, f'{wd}x{ht} below {MIN_IMAGE_SIDE}px minimum')
        if is_gold and not (wd and ht and im.get('phash')):
            rep.add('ERROR', w, 'gold image missing width/height/phash')
    for (i, a), (j, b) in itertools.combinations(enumerate(imgs), 2):
        if N.image_key(a['url']) == N.image_key(b['url']):
            rep.add('ERROR', f'{fid}:images[{i}],[{j}]', 'same image at two sizes (rendition duplicate)')
        else:
            d = N.phash_distance(a.get('phash'), b.get('phash'))
            if d is not None and d <= PHASH_DUP_DISTANCE:
                rep.add('ERROR', f'{fid}:images[{i}],[{j}]', f'visually duplicate (phash distance {d})')

    for k, v in (fam.get('specs') or {}).items():
        _check_spec(v, f'{fid}:specs.{k}', ctx, rep, is_gold, ev)
    if fam.get('specs') and fam.get('spec_source_summary') and fam['spec_source_summary'] != _summary_of(fam):
        rep.add('WARN', f'{fid}:spec_source_summary', f'is {fam["spec_source_summary"]}, sources suggest {_summary_of(fam)}')
    _check_pdf_provenance(ctx, rep, ev)

    for vi, var in enumerate(fam.get('variants', [])):
        for k, v in (var.get('spec_overrides') or {}).items():
            _check_spec(v, f'{fid}:variants[{vi}].spec_overrides.{k}', ctx, rep, is_gold, ev)
        for pi, p in enumerate(var.get('prices', [])):
            w = f'{fid}:variants[{vi}].prices[{pi}]'
            _check_one_source(p.get('source') or {}, w, ctx, rep, is_gold, ev,
                              require_quote=p.get('availability') == 'price_shown')
            if p.get('availability') == 'price_shown' and p.get('amount') is None:
                rep.add('ERROR', w, 'availability=price_shown but amount is null')
            if p.get('availability') != 'price_shown' and p.get('amount') is not None:
                rep.add('ERROR', w, f'amount set but availability={p.get("availability")}')
            if p.get('amount') is not None and not p.get('currency'):
                rep.add('ERROR', w, 'amount without currency')

    if is_gold and not fam.get('variants'):
        rep.add('WARN', fid, 'gold family has no variants listed')


def validate(run, site=None, is_gold=False, evidence_dir=None):
    rep = Report()
    schema_check(run, rep)
    site = site or run.get('site')
    allowed, viewer_hosts = site_hosts(site)
    ev = Evidence(evidence_dir)
    if not ev.enabled:
        rep.add('ERROR' if is_gold else 'WARN', 'evidence',
                f'no evidence text directory ({evidence_dir or "not given"}/text); quotes were not checked')

    seen = {}
    for fam in run.get('families', []):
        k = N.match_key(fam.get('canonical_url', ''))
        if k in seen:
            rep.add('ERROR', fam.get('family_id', '?'), f'duplicate family (same canonical_url as {seen[k]})')
        seen[k] = fam.get('family_id', '?')
        check_family(fam, allowed, viewer_hosts, rep, is_gold, ev)

    if is_gold:
        if not run.get('family_index'):
            rep.add('ERROR', 'family_index', 'gold must include the complete family_index')
        idx = {N.match_key(e['url']) for e in run.get('family_index', [])}
        idx |= {N.match_key(a) for e in run.get('family_index', []) for a in e.get('aliases', [])}
        for fam in run.get('families', []):
            if N.match_key(fam['canonical_url']) not in idx:
                rep.add('ERROR', fam['family_id'], 'labelled family is not in family_index')
        for e in run.get('family_index', []):
            _check_url(e['url'], 'family_index', allowed, viewer_hosts, rep)

    cov = run.get('coverage') or {}
    if cov.get('sitemap_families'):
        n = len(run.get('families', []))
        gap = abs(cov['sitemap_families'] - n) / cov['sitemap_families']
        if gap > SITEMAP_GAP:
            rep.add('WARN', 'coverage', f'{n} families vs {cov["sitemap_families"]} in sitemap ({gap:.0%} gap)')
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('path')
    ap.add_argument('--site')
    ap.add_argument('--gold', action='store_true', help='apply stricter answer-key rules')
    ap.add_argument('--evidence', help='directory containing text/<sha256>.txt snapshots')
    args = ap.parse_args(argv)
    run = load_json(args.path)
    site = args.site or run.get('site')
    evidence = args.evidence
    if evidence is None and args.gold:
        evidence = str(Path(args.path).parent / f'{site}.evidence')
    rep = validate(run, site, args.gold, evidence)
    for sev, where, msg in rep.items:
        print(f'{sev:5} {where}: {msg}')
    print(f'\n{rep.count("ERROR")} error(s), {rep.count("WARN")} warning(s)')
    return 1 if rep.count('ERROR') else 0


if __name__ == '__main__':
    sys.exit(main())
