"""Score an agent's output against a site's answer key (gold).

    # new agent (SiteRun JSON)
    python -m mfr_harness.score --site bray --gold gold/bray.json --pred runs/bray.json
    # existing agent (flat CSV; URL-level metrics only)
    python -m mfr_harness.score --site bray --gold gold/bray.json --legacy ../train/bray/output.csv

Gold is partial: family_index lists every family on the site, but only a sample of families is
fully labelled. Family-level recall/precision use family_index. Asset/spec/price metrics are
computed only inside the labelled families, so they are not affected by families outside the sample.
"""
import argparse
import itertools
import json
import sys

from . import normalize as N
from .config import PRIMARY_DOC_TYPES, load_json, site_hosts
from .legacy import LEGACY_KIND, load_legacy_csv, noise_profile
from .validate import PHASH_DUP_DISTANCE, validate


def ratio(num, den):
    return None if den == 0 else round(num / den, 4)


def prf(tp_gold, n_gold, tp_pred, n_pred):
    return {'recall': ratio(tp_gold, n_gold), 'precision': ratio(tp_pred, n_pred),
            'gold': n_gold, 'pred': n_pred}


# ---------------------------------------------------------------- keys

def doc_key(url):
    return N.match_key(url, drop_asset_params=True)


def index_entries(gold):
    out = []
    for e in gold.get('family_index', []):
        keys = {N.match_key(e['url'])} | {N.match_key(a) for a in e.get('aliases', [])}
        out.append({'url': e['url'], 'keys': keys, 'series': N.norm_token(e.get('series_code') or '') or None})
    return out


def family_keys(fam):
    keys = {N.match_key(fam['canonical_url'])}
    keys |= {N.match_key(a['url']) for a in fam.get('alternates', [])}
    keys |= {N.match_key(v['page_url']) for v in fam.get('variants', []) if v.get('page_url')}
    return keys


def family_series(fam):
    return N.norm_token(fam.get('series_code') or '') or None


def match_family(gold_fam, pred_fams):
    gk, gs = family_keys(gold_fam), family_series(gold_fam)
    best, best_overlap = None, 0
    for pf in pred_fams:
        overlap = len(gk & family_keys(pf)) * 2 + (1 if gs and gs == family_series(pf) else 0)
        if overlap > best_overlap:
            best, best_overlap = pf, overlap
    return best


def same_image(a, b):
    if N.image_key(a['url']) == N.image_key(b['url']):
        return True
    d = N.phash_distance(a.get('phash'), b.get('phash'))
    return d is not None and d <= PHASH_DUP_DISTANCE


def same_doc(a, b):
    if doc_key(a['url']) == doc_key(b['url']):
        return True
    return bool(a.get('sha256')) and a.get('sha256') == b.get('sha256')


def greedy_match(gold_items, pred_items, eq):
    """One-to-one matching; returns list of (gold, pred) pairs."""
    used, pairs = set(), []
    for g in gold_items:
        for i, p in enumerate(pred_items):
            if i not in used and eq(g, p):
                used.add(i)
                pairs.append((g, p))
                break
    return pairs


# ---------------------------------------------------------------- SiteRun scoring

def score_families_index(gold, pred_fams):
    entries = index_entries(gold)
    hits_per_entry = {}
    matched_pred = 0
    for pf in pred_fams:
        pk, ps = family_keys(pf), family_series(pf)
        hits = [i for i, e in enumerate(entries) if e['keys'] & pk or (ps and ps == e['series'])]
        if hits:
            matched_pred += 1
            for i in hits:
                hits_per_entry[i] = hits_per_entry.get(i, 0) + 1
    hit_entries = set(hits_per_entry)
    dup = sum(c - 1 for c in hits_per_entry.values())
    out = prf(len(hit_entries), len(entries), matched_pred, len(pred_fams))
    out['duplicate_families'] = dup
    out['missed_examples'] = [entries[i]['url'] for i in range(len(entries)) if i not in hit_entries][:10]
    return out


def score_labelled(gold, pred_fams):
    acc = {k: [0, 0, 0, 0] for k in ('doc_primary', 'doc_secondary', 'cad', 'image', 'variants')}
    doc_type_ok = doc_type_n = cad_type_ok = cad_type_n = best_version = 0
    pred_img_dups = 0
    spec_scores, spec_missing, spec_extra = {}, {}, 0
    spec_by_source = {'pdf': [], 'page': []}
    conflict = {'tp': 0, 'fn': 0, 'fp': 0}
    refines_seen = [0, 0]   # gold refines, of which pred also said refines
    cited = cite_n = cross_checked = 0
    price = {'variants_with_gold_price': 0, 'availability_correct': 0,
             'amount_checked': 0, 'amount_correct': 0, 'currency_correct': 0, 'price_type_correct': 0}
    unmatched = []

    for gf in gold.get('families', []):
        pf = match_family(gf, pred_fams)
        if pf is None:
            unmatched.append(gf['family_id'])
            pf = {}

        # Matched docs count toward the *gold* tier (a mislabelled doc is still "found");
        # unmatched pred docs are false positives in the tier of their own label.
        g_docs, p_docs = gf.get('documents', []), pf.get('documents', [])
        pairs = greedy_match(g_docs, p_docs, same_doc)
        matched_ids = {id(p) for _, p in pairs}
        for tier in ('doc_primary', 'doc_secondary'):
            def in_tier(d, tier=tier):
                return (d.get('doc_type') in PRIMARY_DOC_TYPES) == (tier == 'doc_primary')
            tp = sum(1 for gd, _ in pairs if in_tier(gd))
            fp = sum(1 for p in p_docs if id(p) not in matched_ids and in_tier(p))
            a = acc[tier]
            a[0] += tp; a[1] += sum(1 for d in g_docs if in_tier(d)); a[2] += tp; a[3] += tp + fp
        for gd, pd in pairs:
            doc_type_n += 1
            doc_type_ok += gd['doc_type'] == pd.get('doc_type')

        pairs = greedy_match(gf.get('cad', []), pf.get('cad', []), lambda a, b: doc_key(a['url']) == doc_key(b['url']))
        a = acc['cad']; a[0] += len(pairs); a[1] += len(gf.get('cad', [])); a[2] += len(pairs); a[3] += len(pf.get('cad', []))
        for gc, pc in pairs:
            cad_type_n += 1
            cad_type_ok += gc['cad_type'] == pc.get('cad_type')

        gi, pi = gf.get('images', []), pf.get('images', [])
        pairs = greedy_match(gi, pi, same_image)
        a = acc['image']; a[0] += len(pairs); a[1] += len(gi); a[2] += len(pairs); a[3] += len(pi)
        for g_img, p_img in pairs:
            if N.match_key(g_img['url']) == N.match_key(p_img['url']):
                best_version += 1
            elif g_img.get('width') and p_img.get('width') and \
                    p_img['width'] * (p_img.get('height') or 1) >= g_img['width'] * (g_img.get('height') or 1):
                best_version += 1
        pred_img_dups += sum(1 for x, y in itertools.combinations(pi, 2) if same_image(x, y))

        gv = {N.norm_token(v['sku']): v for v in gf.get('variants', [])}
        pv = {N.norm_token(v['sku']): v for v in pf.get('variants', [])}
        a = acc['variants']; tp = len(gv.keys() & pv.keys()); a[0] += tp; a[1] += len(gv); a[2] += tp; a[3] += len(pv)

        gspecs, pspecs = gf.get('specs') or {}, pf.get('specs') or {}
        for k, g in gspecs.items():
            # Scored against the displayed gold value (spec sheet wins on conflict).
            score = N.compare_spec(k, g, pspecs[k]) if k in pspecs else 0.0
            if k not in pspecs:
                spec_missing[k] = spec_missing.get(k, 0) + 1
            spec_scores.setdefault(k, []).append(score)
            spec_by_source.setdefault(g.get('display_source') or 'unknown', []).append(score)
            refines_seen[0] += g.get('cross_check') == 'refines'
            refines_seen[1] += g.get('cross_check') == 'refines' and (pspecs.get(k) or {}).get('cross_check') == 'refines'
            g_conf = g.get('cross_check') == 'conflict'
            p_conf = (pspecs.get(k) or {}).get('cross_check') == 'conflict'
            conflict['tp'] += g_conf and p_conf
            conflict['fn'] += g_conf and not p_conf
            conflict['fp'] += p_conf and not g_conf
        spec_extra += len(set(pspecs) - set(gspecs))
        for v in pspecs.values():
            cite_n += 1
            cited += bool(v.get('sources')) and all(s.get('url') for s in v['sources'])
            cross_checked += v.get('cross_check') not in (None, 'not_checked')

        for sku, g_var in gv.items():
            g_prices = g_var.get('prices') or []
            if not g_prices:
                continue
            price['variants_with_gold_price'] += 1
            gp = g_prices[0]
            pp = ((pv.get(sku) or {}).get('prices') or [{}])[0]
            price['availability_correct'] += gp['availability'] == pp.get('availability')
            if gp.get('amount') is not None:
                price['amount_checked'] += 1
                price['amount_correct'] += pp.get('amount') is not None and abs(gp['amount'] - pp['amount']) <= 0.01
                price['currency_correct'] += gp.get('currency') == pp.get('currency')
                price['price_type_correct'] += gp.get('price_type') == pp.get('price_type')

    n_fam = len(gold.get('families', []))
    spec_by_field = {k: round(sum(v) / len(v), 4) for k, v in sorted(spec_scores.items())}
    all_spec = [s for v in spec_scores.values() for s in v]
    return {
        'labelled_families': n_fam,
        'labelled_families_found': n_fam - len(unmatched),
        'unmatched_labelled_families': unmatched,
        'documents_primary': prf(*acc['doc_primary']),
        'documents_secondary': prf(*acc['doc_secondary']),
        'doc_type_accuracy': ratio(doc_type_ok, doc_type_n),
        'cad': prf(*acc['cad']),
        'cad_type_accuracy': ratio(cad_type_ok, cad_type_n),
        'images': prf(*acc['image']),
        'image_best_version_rate': ratio(best_version, acc['image'][0]),
        'image_duplicate_pairs_in_pred': pred_img_dups,
        'variants': prf(*acc['variants']),
        'specs_overall': ratio(sum(all_spec), len(all_spec)),
        'spec_completeness': ratio(len(all_spec) - sum(spec_missing.values()), len(all_spec)),
        'specs_by_field': spec_by_field,
        'specs_by_gold_display_source': {k: ratio(sum(v), len(v)) for k, v in spec_by_source.items()},
        'specs_missing_by_field': spec_missing,
        'specs_extra_unverified': spec_extra,
        'spec_citation_rate': ratio(cited, cite_n),
        'spec_cross_check_rate': ratio(cross_checked, cite_n),
        'refines_detection': {'gold': refines_seen[0], 'pred_agrees': refines_seen[1],
                              'recall': ratio(refines_seen[1], refines_seen[0])},
        'conflict_detection': {**conflict,
                               'recall': ratio(conflict['tp'], conflict['tp'] + conflict['fn']),
                               'precision': ratio(conflict['tp'], conflict['tp'] + conflict['fp'])},
        'price': {**price,
                  'availability_accuracy': ratio(price['availability_correct'], price['variants_with_gold_price']),
                  'amount_accuracy': ratio(price['amount_correct'], price['amount_checked'])},
    }


def score_siterun(gold, pred, site):
    pred_fams = pred.get('families', [])
    rep = validate(pred, site, is_gold=False)
    return {
        'mode': 'siterun',
        'family_index': score_families_index(gold, pred_fams),
        'labelled': score_labelled(gold, pred_fams),
        'spec_violations': {'errors': rep.count('ERROR'), 'warnings': rep.count('WARN'),
                            'first_errors': [f'{w}: {m}' for s, w, m in rep.items if s == 'ERROR'][:15]},
    }


# ---------------------------------------------------------------- legacy scoring

def score_legacy(gold, rows, site):
    allowed, viewer = site_hosts(site)
    page_keys = {N.match_key(u) for u, t in rows if t == 'site_page'}
    any_doc_keys = {doc_key(u) for u, _ in rows}
    type_by_doc_key = {doc_key(u): t for u, t in rows}
    exact_img = {N.match_key(u) for u, t in rows if t == 'image'}
    img_keys = {N.image_key(u) for u, t in rows if t == 'image'}

    entries = index_entries(gold)
    hit = sum(1 for e in entries if e['keys'] & page_keys)
    all_index_keys = set().union(*(e['keys'] for e in entries)) if entries else set()
    pages_on_families = sum(1 for k in page_keys if k in all_index_keys)

    docs = {'primary': [0, 0], 'secondary': [0, 0]}
    doc_label_ok = doc_found = 0
    cad = [0, 0]
    cad_label_ok = 0
    img = {'best_version': 0, 'rendition_only': 0, 'missing': 0}
    for gf in gold.get('families', []):
        for d in gf.get('documents', []):
            tier = 'primary' if d['doc_type'] in PRIMARY_DOC_TYPES else 'secondary'
            docs[tier][1] += 1
            k = doc_key(d['url'])
            if k in any_doc_keys:
                docs[tier][0] += 1
                doc_found += 1
                doc_label_ok += LEGACY_KIND.get(type_by_doc_key[k]) == 'document'
        for c in gf.get('cad', []):
            cad[1] += 1
            k = doc_key(c['url'])
            if k in any_doc_keys:
                cad[0] += 1
                cad_label_ok += LEGACY_KIND.get(type_by_doc_key[k]) == 'cad'
        for im in gf.get('images', []):
            if N.match_key(im['url']) in exact_img:
                img['best_version'] += 1
            elif N.image_key(im['url']) in img_keys:
                img['rendition_only'] += 1
            else:
                img['missing'] += 1
    n_img = sum(img.values())
    return {
        'mode': 'legacy_csv',
        'family_index': {'recall': ratio(hit, len(entries)), 'gold': len(entries),
                         'site_page_rows_that_are_families': ratio(pages_on_families, len(page_keys))},
        'labelled': {
            'documents_primary_recall': ratio(*docs['primary']), 'documents_primary_gold': docs['primary'][1],
            'documents_secondary_recall': ratio(*docs['secondary']), 'documents_secondary_gold': docs['secondary'][1],
            'document_label_correct': ratio(doc_label_ok, doc_found),
            'cad_recall': ratio(*cad), 'cad_gold': cad[1], 'cad_label_correct': ratio(cad_label_ok, cad[0]),
            'images': {**img, 'recall_any_version': ratio(img['best_version'] + img['rendition_only'], n_img),
                       'best_version_rate': ratio(img['best_version'], n_img)},
            'not_scorable': ['specs', 'prices', 'variants', 'precision (no family linkage in legacy format)'],
        },
        'noise': noise_profile(rows, allowed, viewer),
    }


# ---------------------------------------------------------------- CLI

def summarize(report):
    lines = [f"mode: {report['mode']}"]

    def walk(d, indent=0):
        for k, v in d.items():
            if k in ('mode', 'examples', 'missed_examples', 'first_errors'):
                continue
            if isinstance(v, dict):
                lines.append('  ' * indent + f'{k}:')
                walk(v, indent + 1)
            else:
                lines.append('  ' * indent + f'{k}: {v}')
    walk(report)
    return '\n'.join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--site', required=True)
    ap.add_argument('--gold', required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--pred', help='SiteRun JSON from the new agent')
    g.add_argument('--legacy', help='output.csv from the existing agent')
    ap.add_argument('--out', help='write full JSON report here')
    args = ap.parse_args(argv)

    gold = load_json(args.gold)
    if args.pred:
        report = score_siterun(gold, load_json(args.pred), args.site)
    else:
        report = score_legacy(gold, load_legacy_csv(args.legacy), args.site)
    report['site'] = args.site
    if args.out:
        with open(args.out, 'w') as f:
            json.dump(report, f, indent=2)
    print(summarize(report))
    return 0


if __name__ == '__main__':
    sys.exit(main())
