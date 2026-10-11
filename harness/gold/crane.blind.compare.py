"""Compare crane gold with the blind re-label (6 families). Run from harness/:
python gold/crane.blind.compare.py GOLD.json gold/crane.blind.json"""
import json, sys
from collections import defaultdict

def norm(v):
    if isinstance(v, list):
        return tuple(sorted(norm(x) for x in v))
    if isinstance(v, dict):
        return tuple(sorted((k, norm(x)) for k, x in v.items()))
    if isinstance(v, str):
        return ' '.join(v.lower().split())
    return v

def frac(a, b):
    return (len(a & b), len(a | b))

gold = {f['family_id']: f for f in json.load(open(sys.argv[1]))['families']}
blind = {f['family_id']: f for f in json.load(open(sys.argv[2]))['families']}
tot = defaultdict(lambda: [0, 0])
field_rows = defaultdict(lambda: [0, 0])
diffs = []
for fid, b in sorted(blind.items()):
    g = gold[fid]
    gd = {d['url']: d for d in g['documents']}; bd = {d['url']: d for d in b['documents']}
    for k, (n, d) in {'documents found': frac(set(gd), set(bd)),
                      'images': frac({i['url'] for i in g['images']}, {i['url'] for i in b['images']}),
                      'variants': frac({v['sku'] for v in g['variants']}, {v['sku'] for v in b['variants']})}.items():
        if d == 0:
            n = d = 1
        tot[k][0] += n; tot[k][1] += d
    for u in set(gd) & set(bd):
        ok = gd[u]['doc_type'] == bd[u]['doc_type']
        tot['doc_type'][0] += ok; tot['doc_type'][1] += 1
        if not ok:
            diffs.append((fid, 'doc_type', u, gd[u]['doc_type'], bd[u]['doc_type']))
    for fld in sorted(set(g['specs']) | set(b['specs'])):
        gv, bv = g['specs'].get(fld), b['specs'].get(fld)
        ok = gv is not None and bv is not None and norm(gv['value']) == norm(bv['value'])
        field_rows[fld][0] += ok; field_rows[fld][1] += 1
        tot['family spec fields overall'][0] += ok; tot['family spec fields overall'][1] += 1
        if not ok:
            diffs.append((fid, fld, gv and gv['value'], bv and bv['value']))
        if gv is not None and bv is not None:
            okc = gv['cross_check'] == bv['cross_check']
            tot['cross_check'][0] += okc; tot['cross_check'][1] += 1
            if not okc:
                diffs.append((fid, fld + '.cross_check', gv['cross_check'], bv['cross_check']))
for k in ['documents found', 'doc_type', 'images', 'variants', 'cross_check']:
    n, d = tot[k]; print(f'| {k} | {n}/{d} | {100*n/d:.0f}% |')
for fld, (n, d) in sorted(field_rows.items()):
    print(f'| spec: {fld} | {n}/{d} | {100*n/d:.0f}% |')
n, d = tot['family spec fields overall']; print(f'| family spec fields overall | {n}/{d} | {100*n/d:.0f}% |')
print('\nDIFFS')
for x in diffs:
    print(' | '.join(str(y)[:110] for y in x))
