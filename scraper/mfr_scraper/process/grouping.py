"""Evidence-based family grouping (Approach B step 4).

Only pages that each stand for ONE identifier (a part-number page) are candidates for merging; a page that already
lists several models (a whole-family page) stays its own family. Rules, each recorded as evidence:
  R1  same breadcrumb leaf + same model code (identifiers differ only in a trailing size/option number) + same base name
  R2  the same spec sheet/submittal linked from a small set of pages that share breadcrumb leaf and model code
      (a series-wide sheet such as "778 series" does not merge 778V with 778VS: different model codes)
  R3  an "other sizes" / variant block linking the pages to each other (same breadcrumb leaf)
Pages that share leaf and stem but no other evidence are reported as unsure (family_grouping).
"""
import collections
import re

from .. import assets as A
from .. import page as P
from .. import variants as V
from ..pipeline import SPEC_SHEET, base_name
from ..settings import N

GENERIC_CRUMB = re.compile(r'^(home|products?|all products|shop|catalog|store|categories)$', re.I)
SIZE_SECTION = re.compile(r'\b(other|related|available|more|all)\s+(sizes?|models?|variants?|options|part numbers?)\b'
                          r'|^\s*(sizes?|variants?|models?)\s*$|\bselect (a )?(size|model)\b', re.I)
STEM = re.compile(r'^[A-Z]{0,4}\d{2,}')
PART_NO = re.compile(r'^[A-Z]{0,5}\d[A-Z0-9]*(?:[-.][A-Z0-9]+){0,3}$')   # 640WP02, 113-32, 117S2
SHARED_SHEET_MAX = 60


def _norm(s):
    return re.sub(r'\s+', ' ', (s or '').lower()).strip()


def is_identifier(tok):
    tok = (tok or '').strip().upper()
    return V._is_id(tok) or (len(tok) >= 4 and bool(PART_NO.match(tok)) and bool(re.search(r'\d.*\d|[A-Z].*\d|\d.*[A-Z]', tok)))


def identifier_of(rec):
    skus = list(dict.fromkeys(s.strip().upper() for s in rec.skus if is_identifier(s)))
    if len(skus) == 1:
        return skus[0]
    tail = P.path_tail(rec.url).upper()
    return tail if is_identifier(tail) else None


def core_of(ident):
    """Model code without a trailing size / option number: AB100-02 -> AB100, 640WP02 -> 640WP; 778VS stays 778VS."""
    ident = ident or ''
    m = re.match(r'^(.+?)[-_. ](\d{1,3}[A-Z]?)$', ident)
    if m and re.search(r'\d|[A-Z]{2}', m.group(1)):
        return m.group(1)
    m = re.match(r'^(.*\d.*[A-Z])(\d{1,3})$', ident)   # 640WP02 -> 640WP; DA931 is a model number, not DA + size
    return m.group(1) if m else (ident or None)


def stem_of(ident):
    m = STEM.match(ident or '')
    return m.group(0) if m else None


def leaf_of(rec):
    crumbs = [c for c in rec.crumbs if not GENERIC_CRUMB.match(c.strip()) and _norm(c) != _norm(rec.name)
              and c.strip().upper() != (identifier_of(rec) or '')]
    return _norm(crumbs[-1]) if crumbs else ''


def name_key(rec):
    ident = identifier_of(rec) or ''
    words = [w for w in base_name(rec.name or '').split() if w.upper().strip('(),') != ident and not is_identifier(w.strip('(),'))]
    return ' '.join(words).strip(' -–,')


def is_whole_family(rec):
    return len({N.norm_token(s) for s, _, _ in V.from_rows(rec.tables)}) >= 2


def page_info(rec):
    ident = identifier_of(rec)
    return {'identifier': ident, 'stem': stem_of(ident), 'core': core_of(ident), 'leaf': leaf_of(rec), 'name_key': name_key(rec),
            'single': bool(ident) and not is_whole_family(rec)}


def group_pages(recs, ctx_of=lambda r: {}):
    """-> (groups [[rec]], evidence {group index: [str]}, unsure [dict])."""
    n = len(recs)
    parent = list(range(n))
    why = collections.defaultdict(list)

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j, ev):
        a, b = find(i), find(j)
        if a != b:
            parent[b] = a
            why[a] += why.pop(b, [])
        if ev not in why[a]:
            why[a].append(ev)

    info = [page_info(r) for r in recs]
    # R1
    buckets = collections.defaultdict(list)
    for i, inf in enumerate(info):
        if inf['single'] and inf['stem'] and inf['name_key'] and inf['core'] != inf['identifier']:
            buckets[(inf['leaf'], inf['core'], inf['name_key'])].append(i)
    for (leaf, core, nk), idx in buckets.items():
        for j in idx[1:]:
            union(idx[0], j, f'R1 same breadcrumb leaf "{leaf}" + model code "{core}" (identifiers differ only in a size/option number) + base name "{nk}"')
    # R2
    sheet_pages = collections.defaultdict(set)
    sheet_url = {}
    for i, r in enumerate(recs):
        if not info[i]['single']:
            continue
        for u, t in r.doc_links:
            if A.classify_doc(u, t) in SPEC_SHEET:
                k = N.match_key(u, drop_asset_params=True)
                sheet_pages[k].add(i)
                sheet_url[k] = u
    for k, idx in sheet_pages.items():
        if not 2 <= len(idx) <= SHARED_SHEET_MAX:
            continue
        sub = collections.defaultdict(list)
        for i in sorted(idx):
            if info[i]['stem']:
                sub[(info[i]['leaf'], info[i]['core'])].append(i)
        for (leaf, core), lst in sub.items():
            for j in lst[1:]:
                union(lst[0], j, f'R2 shared spec sheet {sheet_url[k]} + breadcrumb leaf "{leaf}" + model code "{core}"')
    # R3
    by_url = {N.match_key(r.url): i for i, r in enumerate(recs)}
    for i, r in enumerate(recs):
        if not info[i]['single']:
            continue
        for u, c in (ctx_of(r) or {}).items():
            sec = c.get('section') or ''
            j = by_url.get(N.match_key(u))
            if j is None or j == i or not SIZE_SECTION.search(sec) or not info[j]['single'] or info[j]['leaf'] != info[i]['leaf']:
                continue
            union(i, j, f'R3 "{sec}" block links the pages (breadcrumb leaf "{info[i]["leaf"]}")')

    roots = collections.OrderedDict()
    for i in range(n):
        roots.setdefault(find(i), []).append(i)
    groups, evidence, root_of_group = [], {}, {}
    for root, idx in roots.items():
        idx.sort(key=lambda i: _natural(info[i]['identifier'] or recs[i].url))
        gi = len(groups)
        groups.append([recs[i] for i in idx])
        root_of_group[root] = gi
        if len(idx) > 1:
            evidence[gi] = why.get(root, [])

    # unsure: same leaf + stem split into several groups with no merge evidence
    unsure = []
    seen = collections.defaultdict(set)
    for i, inf in enumerate(info):
        if inf['single'] and inf['stem'] and inf['leaf']:
            seen[(inf['leaf'], inf['stem'])].add(root_of_group[find(i)])
    for (leaf, stem), gis in seen.items():
        if len(gis) < 2:
            continue
        gis = sorted(gis)
        names = {gi: info[recs.index(groups[gi][0])]['name_key'] for gi in gis}
        for gi in gis[1:]:
            unsure.append({'group': gi, 'other_group': gis[0], 'leaf': leaf, 'stem': stem,
                           'name': names[gi], 'other_name': names[gis[0]]})
    return groups, evidence, unsure


def _natural(s):
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', s or '')]
