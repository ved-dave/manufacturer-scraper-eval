"""Reproducible 15-family sample for the apollo answer key (DEVIN_TASK step 3).

Run from harness/:  python gold/apollo.sample.py
Reads family_index (+ per-family category / coverage attributes) from gold/apollo.family_index_meta.json.

STATUS 2026-10-11: aalberts-ips.us served a LiteSpeed reCAPTCHA "Bot Verification" wall to every request
(HTTP client and a normal Chrome browser), so no family index could be built and the meta file is empty.
The procedure below is fixed in advance so a later labeller draws the same sample once the site is reachable.

Procedure (same as gold/bray.sample.py):
1. Apollo-branded families only (brand rule in apollo.ambiguities.md); other Aalberts brands are not in the meta file.
2. Group by top-level category (the site's product navigation menu).
3. Allocate 15 draws in proportion to category size (largest-remainder; ties broken by category name).
4. Within each category (visited alphabetically) draw with ONE random.Random(42) instance over the families
   sorted by URL.
5. Coverage swaps (>= 3 CAD/BIM, >= 3 multi-variant, >= 1 with price info): replace the *last* drawn
   non-qualifying family of the largest category with the first qualifying undrawn family of that category
   (after random.Random(42).shuffle of the qualifying pool); fall back to the next-largest category. Each swap
   is printed and logged in apollo.ambiguities.md.
"""
import json
import random
from collections import defaultdict
from pathlib import Path

N = 15
SEED = 42
META = Path(__file__).with_name('apollo.family_index_meta.json')
REQUIREMENTS = (
    ('cad_bim', 3, lambda f: f.get('has_cad')),
    ('multi_variant', 3, lambda f: f.get('n_variants', 0) > 1),
    ('price_info', 1, lambda f: f.get('has_price')),
)


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
    if not fams:
        print('family index is empty (site blocked); nothing to draw')
        return [], []
    by_cat = defaultdict(list)
    for f in sorted(fams, key=lambda f: f['url']):
        by_cat[f['category']].append(f)
    alloc = allocate({c: len(v) for c, v in by_cat.items()}, min(N, len(fams)))
    rng = random.Random(SEED)
    drawn = []
    for cat in sorted(by_cat):
        for f in rng.sample(by_cat[cat], alloc[cat]):
            drawn.append(dict(f, _cat=cat))
    cats_by_size = sorted(by_cat, key=lambda c: (-len(by_cat[c]), c))
    swaps = []
    for label, need, req in REQUIREMENTS:
        def short():
            return sum(1 for f in drawn if req(f)) < need
        if not short():
            continue
        protected = [r for lbl, _, r in REQUIREMENTS if lbl != label]
        for cat in cats_by_size:
            taken = {d['url'] for d in drawn}
            pool = [f for f in by_cat[cat] if f['url'] not in taken and req(f)]
            random.Random(SEED).shuffle(pool)
            while short() and pool:
                cands = [i for i, d in enumerate(drawn) if d['_cat'] == cat and not req(d)
                         and not any(p(d) for p in protected)]
                if not cands:
                    break
                idx = max(cands)
                old, new = drawn[idx], dict(pool.pop(0), _cat=cat)
                drawn[idx] = new
                swaps.append((label, old['url'], new['url']))
            if not short():
                break
        if short():
            print(f'coverage {label}: only {sum(1 for f in fams if req(f))} qualifying families site-wide')
    for f in drawn:
        print(f"{f['_cat']:40} {f['url']:70} variants={f.get('n_variants', 0):3} cad={f.get('has_cad')} {f['name']}")
    for s in swaps:
        print('SWAP', *s)
    return drawn, swaps


if __name__ == '__main__':
    main()
