"""Reproducible 15-family sample for the crane answer key (DEVIN_TASK step 3).

Run from harness/:  python gold/crane.sample.py
Reads family_index (+ per-family category / coverage attributes) from gold/crane.family_index_meta.json,
which is derived from the same crawl as gold/crane.json -> family_index.

Procedure:
1. Group the index by top-level category (second breadcrumb item = top-level nav menu: General Valves, Connected Solutions, Pipe Fittings, ProBalance, Public Health Valves). n_variants in the meta file = identifiers in the page heading (title codes) when there are 2+, else 0; has_cad = a BIM (bimstore) link in Downloads).
   n_variants is the sampling-time proxy only; the labelled variant counts in crane.json follow SPEC 3 (sheet part-number
   tables count too, e.g. D103B has 8), see crane.ambiguities.md.
2. Allocate 15 draws in proportion to category size (largest-remainder method; ties broken by category name).
3. Within each category, draw with random.Random(42) over the families sorted by URL. One RNG instance is used
   for all categories, visited in alphabetical order, so the whole draw is reproducible.
4. Coverage swaps: if fewer than 3 families have CAD/BIM or fewer than 3 have >1 variant, replace the *last*
   drawn non-qualifying family in the largest category with the first qualifying undrawn family of that category
   (after a fresh Random(42).shuffle of the qualifying pool). If the largest category runs out of qualifying
   families or drawn slots, continue with the next-largest category. Fallback: if no same-category swap can
   close the gap (all qualifying families sit in a category whose drawn slots already qualify), fall back to the
   literal DEVIN_TASK rule: replace the *last* drawn non-qualifying family of the largest category with the first
   qualifying undrawn family from the whole index (after Random(42).shuffle). Each swap is printed and logged in
   ambiguities.md. A requirement the site cannot meet (fewer than 3 qualifying families site-wide) is reported.
"""
import json
import random
from collections import defaultdict
from pathlib import Path

N = 15
SEED = 42
META = Path(__file__).with_name('crane.family_index_meta.json')


def allocate(sizes, n):
    total = sum(sizes.values())
    quotas = {c: n * s / total for c, s in sizes.items()}
    alloc = {c: int(q) for c, q in quotas.items()}
    rest = n - sum(alloc.values())
    for c in sorted(quotas, key=lambda c: (-(quotas[c] - alloc[c]), c))[:rest]:
        alloc[c] += 1
    return alloc


def main():
    fams = json.loads(META.read_text())
    by_cat = defaultdict(list)
    for f in sorted(fams, key=lambda f: f['url']):
        by_cat[f['category']].append(f)
    alloc = allocate({c: len(v) for c, v in by_cat.items()}, N)
    rng = random.Random(SEED)
    drawn = []
    for cat in sorted(by_cat):
        k = alloc[cat]
        if k:
            for f in rng.sample(by_cat[cat], k):
                drawn.append(dict(f, _cat=cat))
    # Swap target: the largest category (DEVIN_TASK step 3). If it has no undrawn family meeting the requirement,
    # fall back to the next-largest category, and so on (logged in ambiguities.md).
    cats_by_size = sorted(by_cat, key=lambda c: (-len(by_cat[c]), c))
    swaps = []

    def short(req):
        return sum(1 for f in drawn if req(f)) < 3

    for label, req in (('cad_bim', lambda f: f['has_cad']), ('multi_variant', lambda f: f['n_variants'] > 1)):
        if not short(req):
            continue
        if not any(req(f) for f in fams):
            print(f'coverage {label}: site has none; requirement waived')
            continue
        for cat in cats_by_size:
            taken = {d['url'] for d in drawn}
            pool = [f for f in by_cat[cat] if f['url'] not in taken and req(f)]
            random.Random(SEED).shuffle(pool)
            while short(req) and pool:
                cands = [i for i, d in enumerate(drawn) if d['_cat'] == cat and not req(d)]
                if not cands:
                    break
                idx = max(cands)
                old, new = drawn[idx], dict(pool.pop(0), _cat=cat)
                drawn[idx] = new
                swaps.append((label, old['url'], new['url']))
            if not short(req):
                break
        taken = {d['url'] for d in drawn}
        pool = [f for f in sorted(fams, key=lambda f: f['url']) if f['url'] not in taken and req(f)]
        random.Random(SEED).shuffle(pool)
        for cat in cats_by_size:
            while short(req) and pool:
                cands = [i for i, d in enumerate(drawn) if d['_cat'] == cat and not req(d)]
                if not cands:
                    break
                idx = max(cands)
                old, new = drawn[idx], dict(pool.pop(0))
                new['_cat'] = new['category']
                drawn[idx] = new
                swaps.append((label + ' (cross-category)', old['url'], new['url']))
            if not short(req):
                break
        if short(req):
            n = sum(1 for f in fams if req(f))
            print(f'coverage {label}: only {n} qualifying families site-wide; {sum(1 for f in drawn if req(f))} in sample')
    print('allocation:', json.dumps({c: alloc[c] for c in sorted(alloc) if alloc[c]}, indent=1))
    for f in drawn:
        print(f"{f['_cat']:45} {f['url']:60} variants={f['n_variants']:3} cad={f['has_cad']} {f['name']}")
    for s in swaps:
        print('SWAP', *s)
    print('cad/bim:', sum(f['has_cad'] for f in drawn), ' multi-variant:', sum(f['n_variants'] > 1 for f in drawn))
    return drawn, swaps


if __name__ == '__main__':
    main()
