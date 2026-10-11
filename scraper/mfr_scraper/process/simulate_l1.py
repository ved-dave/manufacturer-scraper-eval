"""Build an L1 link file from an L0 CSV plus our own fetch cache: what the old agent would emit if it recorded
the OLD_AGENT_IMPROVEMENTS.md fields while crawling. Used only to measure L1 against L0 (REPORT_APPROACH_B.md).

Only URLs in the old agent's inventory are emitted (no discovery is added). Pages we never fetched get a page
record without html_snapshot, so the processor fetches them as it would for a real L1 file with gaps.

    python -m mfr_scraper.process.simulate_l1 --site bray --links ../train/bray/output.csv --out ../harness/runs/L1/bray.jsonl
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import quote

from .. import assets as A
from .. import page as P
from ..settings import CACHE_DIR
from .context import canonical_of, link_context
from .readers import read_l0

L1_TYPE = {'page': 'page', 'pdf': 'pdf', 'image': 'image', 'cad': 'cad', 'bim': 'bim', 'archive': 'archive',
           'spreadsheet': 'spreadsheet', 'video': 'video'}


def cached(site, url):
    key = hashlib.sha1(f'GET {url}'.encode()).hexdigest()
    for d in (CACHE_DIR / f'{site}.process', CACHE_DIR / site):
        m = d / f'{key}.json'
        if m.exists():
            meta = json.loads(m.read_text())
            b = d / f'{key}.body'
            return meta, (b.read_bytes() if b.exists() else b'')
    return None, None


def file_facts(meta, body):
    if not meta:
        return {}
    h = meta.get('headers') or {}
    n = h.get('content-length')
    return {'status': meta.get('status'), 'final_url': meta.get('final_url'), 'content_type': h.get('content-type'),
            'content_length': int(n) if n and str(n).isdigit() else (len(body) if body else None),
            'last_modified': h.get('last-modified'), 'etag': h.get('etag')}


def page_facts(soup, final):
    h1 = soup.find('h1')
    ld = next((o for o in P.jsonld_objects(soup) if P.ld_type_is(o, 'Product')), None)
    return {'page_title': P.text_of(soup.title) if soup.title else None, 'h1': P.text_of(h1) if h1 else None,
            'breadcrumb': P.breadcrumbs(soup) or None, 'canonical_url': canonical_of(soup, final),
            'lang': P.html_lang(soup) or None,
            'hreflang': {k: quote(v, safe=":/?&=%#+,;@!$'()*~") for k, v in P.hreflang_alternates(soup, final).items()} or None,
            'jsonld_product': ld, 'has_spec_table': len(P.label_value_pairs(soup)) >= 3}


def build(site, links_path, out):
    out = Path(out)
    snaps = out.parent / f'{out.stem}.snapshots'
    snaps.mkdir(parents=True, exist_ok=True)
    ls = read_l0(links_path)
    inv = {l.url: L1_TYPE.get(l.url_type, 'other') for l in ls.links}
    inv.update({u: 'page' for u in ls.pages})
    stats = {'pages': 0, 'snapshots': 0, 'links': 0, 'assets_with_found_on': 0, 'assets_orphan': 0}
    seen_assets, recs = set(), []
    for url in ls.pages:
        meta, body = cached(site, url)
        rec = {'record': 'page', 'site': site, 'url': url, 'status': meta.get('status') if meta else None}
        stats['pages'] += 1
        if meta and meta.get('status') == 200 and 'html' in ((meta.get('headers') or {}).get('content-type') or 'text/html'):
            final = meta.get('final_url') or url
            soup = P.soup_of(body.decode('utf-8', errors='replace'))
            snap = snaps / f'{hashlib.sha256(body).hexdigest()}.html'
            snap.write_bytes(body)
            rec.update(file_facts(meta, body))
            rec.update(page_facts(soup, final))
            rec['html_snapshot'] = f'{snaps.name}/{snap.name}'
            if rec.get('content_length') is None:
                rec['content_length'] = len(body)
            stats['snapshots'] += 1
            recs.append(rec)
            for u, c in link_context(soup, final).items():
                t = inv.get(u)
                if not t:
                    continue
                link = {'record': 'link', 'site': site, 'url': u, 'url_type': t, 'found_on': url, **c}
                if t != 'page':
                    seen_assets.add(u)
                    am, ab = cached(site, u)
                    link.update(file_facts(am, ab))
                    if t == 'image':
                        link['alt'] = c.get('link_text')
                        if ab:
                            w, h, _ = A.image_dims_phash(ab)
                            link['width'], link['height'] = w, h
                recs.append({k: v for k, v in link.items() if v is not None or k == 'found_on'})
                stats['links'] += 1
        else:
            recs.append(rec)
    stats['assets_with_found_on'] = len(seen_assets)
    orphans = [u for u, t in inv.items() if t != 'page' and u not in seen_assets]
    stats['assets_orphan'] = len(orphans)
    for u in orphans:   # listed by the old agent on a page we hold no copy of: inventory-only record
        am, ab = cached(site, u)
        recs.append({k: v for k, v in {'record': 'link', 'site': site, 'url': u, 'url_type': inv[u], 'found_on': None,
                                        **file_facts(am, ab)}.items() if v is not None or k == 'found_on'})
    with open(out, 'w') as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    return stats, orphans


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--site', required=True)
    ap.add_argument('--links', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    stats, orphans = build(a.site, a.links, a.out)
    print(json.dumps(stats), 'orphan examples:', orphans[:5])


if __name__ == '__main__':
    main()
