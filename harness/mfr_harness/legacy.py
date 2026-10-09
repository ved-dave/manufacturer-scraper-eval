"""Read the existing agent's flat output.csv (url,url_type) and describe it in spec v1 terms.

The legacy format has no family linkage, specs, or prices, so it can only be scored at URL level.
"""
import collections
import csv

from . import normalize as N

# legacy url_type -> v1 asset kind ('page', 'document', 'cad', 'image', 'unknown')
LEGACY_KIND = {
    'site_page': 'page',
    'pdf': 'document',
    'spreadsheet': 'document',
    'image': 'image',
    'cad': 'cad',
    'bim': 'cad',
    'archive': 'unknown',   # zips: may or may not be CAD
    'document': 'unknown',  # used for listing pages and CAD viewers alike
}


def load_legacy_csv(path):
    with open(path, encoding='utf-8', errors='replace', newline='') as f:
        return [(r['url'].strip(), r['url_type'].strip()) for r in csv.DictReader(f) if r.get('url')]


def noise_profile(rows, allowed_hosts, viewer_hosts):
    """Rows that spec v1 would drop or collapse, before any gold comparison."""
    non_en = [u for u, _ in rows if not N.is_english(N.locale_of_url(u))]
    off = [u for u, t in rows if not N.host_allowed(u, allowed_hosts + viewer_hosts)]
    imgs = [u for u, t in rows if t == 'image']
    img_keys = collections.Counter(N.image_key(u) for u in imgs)
    rendition_dups = sum(c - 1 for c in img_keys.values())
    by_type = collections.Counter(t for _, t in rows)
    return {
        'rows': len(rows),
        'by_type': dict(by_type),
        'non_english_rows': len(non_en),
        'off_allowlist_rows': len(off),
        'image_rendition_duplicates': rendition_dups,
        'unknown_kind_rows': sum(1 for _, t in rows if LEGACY_KIND.get(t, 'unknown') == 'unknown'),
        'examples': {'non_english': non_en[:5], 'off_allowlist': off[:5]},
    }
