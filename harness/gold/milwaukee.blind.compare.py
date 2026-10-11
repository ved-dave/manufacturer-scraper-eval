"""Compare milwaukee gold with the blind re-label (6 families). Run from harness/:
python gold/milwaukee.blind.compare.py gold/milwaukee.json BLIND_DIR
BLIND_DIR holds one <family_id>.json per re-labelled family (format in the blind brief)."""
import json, sys, os, re
from urllib.parse import unquote
from collections import defaultdict


def norm(v):
    if isinstance(v, list):
        return tuple(sorted(norm(x) for x in v))
    if isinstance(v, dict):
        return tuple(sorted((k, norm(x)) for k, x in v.items() if x is not None))
    if isinstance(v, str):
        v = ' '.join(v.lower().replace('\u2013', '-').split())
        return re.sub(r'^(\d+) (\d+/\d+)$', r'\1-\2', v)
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def fname(u):
    return unquote(u.split('?')[0].rsplit('/', 1)[-1]).lower()


def frac(a, b):
    return (len(a & b), len(a | b)) if a | b else (1, 1)


gold = {'milwaukee-' + re.sub(r'[^a-z0-9]+', '-', f['family_id'].lower()).strip('-'): f for f in json.load(open(sys.argv[1]))['families']}
bdir = sys.argv[2]
tot = defaultdict(lambda: [0, 0])
diffs = []
for fn in sorted(os.listdir(bdir)):
    if not fn.endswith('.json'):
        continue
    fid = fn[:-5]
    g, b = gold[fid], json.load(open(os.path.join(bdir, fn)))
    # price_list documents are compared through variant prices, not as documents
    gd = {fname(d['url']): d['doc_type'] for d in g['documents'] if d['doc_type'] != 'price_list'}
    bd = {unquote(d['filename']).lower(): d['doc_type'] for d in b['documents'] if d['doc_type'] != 'price_list'}
    gc = {(c['url'].split('&TB_iframe')[0], bool(c.get('gated'))) for c in g['cad']}
    bc = {(c['url'].split('&TB_iframe')[0], bool(c.get('gated'))) for c in b['cad']}
    gi = {(i['url'], i.get('image_type')) for i in g['images']}
    bi = {(i['url'], i.get('image_type')) for i in b['images'] if i.get('keep')}
    gv = {norm(v['sku']) for v in g['variants']}
    bv = {norm(v['sku']) for v in b['variants']}
    go = {(norm(s), f, norm(x['value'])) for s, o in (g.get('variant_overrides') or {}).items() for f, x in o.items()}
    go |= {(norm(v['sku']), f, norm(x['value'])) for v in g['variants'] for f, x in (v.get('spec_overrides') or {}).items()}
    bo = {(norm(s), f, norm(x['value'])) for s, o in (b.get('variant_overrides') or {}).items() for f, x in o.items()}
    for k, (a, c), (ga, ba) in (('variants', frac(gv, bv), (gv, bv)), ('documents', frac(set(gd), set(bd)), (set(gd), set(bd))),
                                ('CAD', frac(gc, bc), (gc, bc)), ('images', frac(gi, bi), (gi, bi)),
                                ('variant overrides', frac(go, bo), (go, bo))):
        tot[k][0] += a; tot[k][1] += c
        if ga ^ ba:
            diffs.append((fid, k, 'gold only', sorted(map(str, ga - ba)), 'blind only', sorted(map(str, ba - ga))))
    for d in set(gd) & set(bd):
        ok = gd[d] == bd[d]
        tot['doc_type'][0] += ok; tot['doc_type'][1] += 1
        if not ok:
            diffs.append((fid, 'doc_type', d, gd[d], bd[d]))
    gs, bs = g['specs'], b.get('specs') or {}
    for f in sorted(set(gs) | set(bs)):
        x, y = gs.get(f), bs.get(f)
        ok = x is not None and y is not None and norm(x['value']) == norm(y['value'])
        tot['family spec fields'][0] += ok; tot['family spec fields'][1] += 1
        if not ok:
            diffs.append((fid, f, x and x['value'], y and y['value']))
        if x is not None and y is not None:
            okc = x['cross_check'] == y.get('cross_check')
            tot['cross_check'][0] += okc; tot['cross_check'][1] += 1
            if not okc:
                diffs.append((fid, f + '.cross_check', x['cross_check'], y.get('cross_check')))
print('| dimension | agree | % |\n|---|---|---|')
for k in ['variants', 'documents', 'doc_type', 'CAD', 'images', 'family spec fields', 'variant overrides', 'cross_check']:
    a, c = tot[k]
    print(f'| {k} | {a}/{c} | {100 * a / c:.0f}% |' if c else f'| {k} | 0/0 | n/a |')
print('\nDIFFS')
for x in diffs:
    print(' | '.join(str(y)[:160] for y in x))
