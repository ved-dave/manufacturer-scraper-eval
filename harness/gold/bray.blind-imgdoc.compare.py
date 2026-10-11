"""Compare the blind Bray image/doc_type re-label with the Bray answer key.

Usage (from harness/): python gold/bray.blind-imgdoc.compare.py [gold.json] [blind.json]
Documents match on normalised URL (score.doc_key rule) or sha256; images on image_key or phash <= 2.
Agreement on sets = matched / (gold + blind - matched); on labels = same label / matched.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from mfr_harness import normalize as N  # noqa: E402

PHASH_MAX = 2
HERE = os.path.dirname(os.path.abspath(__file__))


def doc_same(a, b):
    if N.match_key(a['url'], drop_asset_params=True) == N.match_key(b['url'], drop_asset_params=True):
        return True
    return bool(a.get('sha256')) and a.get('sha256') == b.get('sha256')


def img_same(a, b):
    if N.image_key(a['url']) == N.image_key(b['url']):
        return True
    d = N.phash_distance(a.get('phash'), b.get('phash'))
    return d is not None and d <= PHASH_MAX


def match(gold, blind, eq):
    pairs, used = [], set()
    for g in gold:
        for j, b in enumerate(blind):
            if j not in used and eq(g, b):
                pairs.append((g, b))
                used.add(j)
                break
    return pairs


def name(u):
    return u.split('?')[0].rstrip('/').split('/')[-1]


def main():
    gpath = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'bray.json')
    bpath = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'bray.blind-imgdoc.json')
    gold = {f['family_id']: f for f in json.load(open(gpath))['families']}
    blind = json.load(open(bpath))['families']
    tot = dict(dg=0, db=0, dm=0, dt=0, ig=0, ib=0, im=0, it=0)
    rows, diffs = [], []
    for bf in blind:
        fid = bf['family_id']
        gf = gold[fid]
        gd, bd = gf.get('documents', []), bf.get('documents', [])
        gi, bi = gf.get('images', []), bf.get('images', [])
        dp = match(gd, bd, doc_same)
        ip = match(gi, bi, img_same)
        dt = sum(g['doc_type'] == b['doc_type'] for g, b in dp)
        it = sum(g['image_type'] == b['image_type'] for g, b in ip)
        for g, b in dp:
            if g['doc_type'] != b['doc_type']:
                diffs.append(f"{fid}: doc_type {name(g['url'])}: gold={g['doc_type']} blind={b['doc_type']}")
        for g, b in ip:
            if g['image_type'] != b['image_type']:
                diffs.append(f"{fid}: image_type {name(g['url'])}: gold={g['image_type']} blind={b['image_type']}")
        mg = {id(g) for g, _ in dp}
        mb = {id(b) for _, b in dp}
        diffs += [f"{fid}: document gold-only {name(x['url'])}" for x in gd if id(x) not in mg]
        diffs += [f"{fid}: document blind-only {name(x['url'])}" for x in bd if id(x) not in mb]
        mg = {id(g) for g, _ in ip}
        mb = {id(b) for _, b in ip}
        diffs += [f"{fid}: image gold-only {name(x['url'])} {x.get('width')}x{x.get('height')}" for x in gi if id(x) not in mg]
        diffs += [f"{fid}: image blind-only {name(x['url'])} {x.get('width')}x{x.get('height')}" for x in bi if id(x) not in mb]
        rows.append((fid, len(gd), len(bd), len(dp), dt, len(gi), len(bi), len(ip), it))
        for k, v in zip(('dg', 'db', 'dm', 'dt', 'ig', 'ib', 'im', 'it'), rows[-1][1:]):
            tot[k] += v

    def pct(a, b):
        return f"{a}/{b} ({100 * a / b:.0f}%)" if b else 'n/a'

    print('| Family | Docs gold/blind/matched | doc_type same | Images gold/blind/matched | image_type same |')
    print('|---|---|---|---|---|')
    for fid, g, b, m, t, ig, ib, im, it in rows:
        print(f'| {fid} | {g}/{b}/{m} | {t}/{m} | {ig}/{ib}/{im} | {it}/{im} |')
    print()
    print('| Row | Agreement |')
    print('|---|---|')
    print(f"| Documents (same PDFs, matched / union) | {pct(tot['dm'], tot['dg'] + tot['db'] - tot['dm'])} |")
    print(f"| doc_type (same label / matched docs) | {pct(tot['dt'], tot['dm'])} |")
    print(f"| Images (same images, matched / union) | {pct(tot['im'], tot['ig'] + tot['ib'] - tot['im'])} |")
    print(f"| image_type (same label / matched images) | {pct(tot['it'], tot['im'])} |")
    print()
    print('Disagreements:')
    for d in diffs or ['(none)']:
        print('-', d)


if __name__ == '__main__':
    main()
