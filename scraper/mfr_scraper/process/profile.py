"""Site profile: before grouping, find how the manufacturer itself defines a product family.

A small sample of pages (snapshots / fetch cache) is read and four family shapes are tested:
  family_pages    one page lists several part numbers (Bray, Crane): each page is a family
  category_cards  category pages show cards, each with a family name and one part number (Sioux Chief)
  item_tables     a part-number page lists sibling part numbers in its own table
  shared_sheet    several part-number pages link the same spec sheet
Each shape is scored by coverage (share of sampled product pages it explains) and contradictions. The chosen shape,
its evidence and (for category_cards) the card families are written to <site>.profile.json, a readable data file.
Grouping follows it (process --profile); the R1-R4 rules only fill gaps. Answer keys are never read.
"""
import collections
import json
import re
from pathlib import Path
from urllib.parse import urljoin

from .. import assets as A
from .. import discover as D
from .. import page as P
from ..pipeline import SPEC_SHEET, now_iso
from ..settings import N, PRODUCT_SCORE_THRESHOLD
from . import grouping as G

PROFILE_VERSION = 'sp-1'
MIN_CARDS = 4
MAX_CARD_TEXT = 600
SAMPLE_PER_TEMPLATE = 5
MAX_TEMPLATES = 40
CARD_TEMPLATE_SHARE = 0.6
MAX_CARD_PAGES = 3000
PRODUCT_SAMPLE = 50
CARD_MIN_COVERAGE = 0.7
CARD_MAX_CONTRADICTIONS = 0.1
FAMILY_PAGE_MIN = 0.5
IDENT_LABEL = re.compile(r'\b(?:item|part|model|catalog|cat\.?|sku|product|order(?:ing)?)\s*(?:number|no\.?|#|code)?\s*[:#]\s*'
                         r'([A-Z0-9][A-Z0-9\-./]*[A-Z0-9])', re.I)


def _txt(el):
    return re.sub(r'\s+', ' ', el.get_text(' ', strip=True)).strip()


def _norm_name(s):
    return re.sub(r'\s+', ' ', (s or '').lower()).strip()


def card_ident(el):
    m = IDENT_LABEL.search(_txt(el))
    if m and G.is_identifier(m.group(1)):
        return m.group(1).upper()
    for img in el.find_all('img', alt=True):
        alt = img['alt'].strip()
        if G.is_identifier(alt):
            return alt.upper()
    return None


def _card_link(el, url):
    a = el if el.name == 'a' and el.get('href') else el.find('a', href=True)
    return urljoin(url, a['href']) if a else None


def card_candidates(soup, url):
    """-> {class token: [card]}: repeated small elements that each carry a link and a part number."""
    by_tok = collections.defaultdict(list)
    for el in soup.find_all(True, class_=True):
        for c in el.get('class', []):
            by_tok[c].append(el)
    out = {}
    for tok, els in by_tok.items():
        if len(els) < MIN_CARDS:
            continue
        cards = []
        for el in els:
            text = _txt(el)
            if not text or len(text) > MAX_CARD_TEXT or el.find(class_=tok):
                continue
            href, ident = _card_link(el, url), card_ident(el)
            if not href or not ident:
                continue
            fields = {}
            for d in el.find_all(True, class_=True):
                t = _txt(d)
                if t and len(t) <= 120:
                    for c in d.get('class', []):
                        fields.setdefault(c, t)
            cards.append({'href': href, 'ident': ident, 'fields': fields})
        if len(cards) >= MIN_CARDS:
            out[tok] = cards
    return out


def learn_card_spec(pages):
    """pages: [(url, soup)] -> {'card_class', 'name_class', ...} or None.
    A card shape names families when one child text is shared by several cards on a page (the family name)."""
    stats = collections.defaultdict(lambda: {'cards': 0, 'repeats': 0, 'names': set(), 'pages': 0, 'example': None})
    for url, soup in pages:
        for tok, cards in card_candidates(soup, url).items():
            per_name_tok = collections.defaultdict(list)
            for c in cards:
                for ntok, t in c['fields'].items():
                    if ntok != tok and c['ident'] not in t.upper() and not G.is_identifier(t) and 3 <= len(t) <= 80:
                        per_name_tok[ntok].append(t)
            for ntok, names in per_name_tok.items():
                s = stats[(tok, ntok)]
                s['cards'] += len(names)
                s['repeats'] += len(names) - len(set(names))
                s['names'].update(names)
                s['pages'] += 1
                s['example'] = s['example'] or {'page': url, 'name': names[0]}
    best = None
    for (tok, ntok), s in stats.items():
        if s['repeats'] < 0.2 * s['cards'] or len(s['names']) < 2 or s['pages'] < 2:
            continue
        if best is None or s['cards'] > best[1]['cards']:
            best = ((tok, ntok), s)
    if not best:
        return None
    (tok, ntok), s = best
    return {'card_class': tok, 'name_class': ntok, 'cards_in_sample': s['cards'], 'pages_in_sample': s['pages'],
            'distinct_names_in_sample': len(s['names']), 'example': s['example']}


def extract_cards(soup, url, spec):
    out = []
    for el in soup.find_all(class_=spec['card_class']):
        if el.find(class_=spec['card_class']):
            continue
        n = el.find(class_=spec['name_class'])
        href, ident = _card_link(el, url), card_ident(el)
        if n is not None and href and ident:
            out.append({'name': _txt(n), 'ident': ident, 'href': href, 'page': url})
    return out


def card_families(cards):
    """One family per (category page, card name). A part number listed on several category pages belongs to the most
    specific one (fewest cards): parent categories repeat their sub-categories' cards under the same names."""
    size = collections.Counter(c['page'] for c in cards)
    home = {}
    for c in cards:
        k = (c['page'], _norm_name(c['name']))
        cur = home.get(c['ident'])
        if cur is None or size[k[0]] < size[cur[0]]:
            home[c['ident']] = k
    fams = collections.OrderedDict()
    for c in cards:
        k = (c['page'], _norm_name(c['name']))
        if home[c['ident']] != k:
            continue
        f = fams.setdefault(k, {'name': c['name'], 'source_pages': [c['page']], 'members': []})
        if c['ident'] not in f['members']:
            f['members'].append(c['ident'])
    return list(fams.values())


def score_shapes(products, families, site_idents):
    """products: sampled product PageRecs. -> {shape: {coverage, contradictions, examples}}"""
    n = len(products) or 1
    info = [G.page_info(r) for r in products]
    singles = [(r, inf) for r, inf in zip(products, info) if inf['single']]
    out = {}
    whole = [r.url for r, inf in zip(products, info) if not inf['single']]   # lists several models, or names a series
    out['family_pages'] = {'coverage': len(whole) / n, 'contradictions': 0.0, 'examples': whole[:3]}
    out['model_pages'] = {'coverage': len(singles) / n, 'contradictions': 0.0, 'examples': [r.url for r, _ in singles[:3]]}
    member_of = collections.defaultdict(set)
    for i, f in enumerate(families):
        for m in f['members']:
            member_of[m].add(i)
    covered = [(r, inf) for r, inf in zip(products, info) if inf['identifier'] in member_of]
    contra = [r.url for r, inf in covered if len({_norm_name(families[i]['name']) for i in member_of[inf['identifier']]}) > 1]
    out['category_cards'] = {'coverage': len(covered) / n, 'contradictions': len(contra) / (len(covered) or 1),
                             'examples': [f'{r.url} is card "{families[min(member_of[inf["identifier"]])]["name"]}"'
                                          for r, inf in covered[:3]]}
    tab = [r.url for r, inf in singles
           if ({c.strip().upper() for row in r.tables for c in row} & site_idents) - {inf['identifier']}]
    out['item_tables'] = {'coverage': len(tab) / n, 'contradictions': 0.0, 'examples': tab[:3]}
    sheets = collections.defaultdict(set)
    for r, inf in singles:
        for u, t in r.doc_links:
            if A.classify_doc(u, t) in SPEC_SHEET:
                sheets[N.match_key(u, drop_asset_params=True)].add(r.url)
    shared = sorted({u for us in sheets.values() if len(us) > 1 for u in us})
    out['shared_sheet'] = {'coverage': len(shared) / n, 'contradictions': 0.0, 'examples': shared[:3]}
    for v in out.values():
        v['coverage'], v['contradictions'] = round(v['coverage'], 3), round(v['contradictions'], 3)
    return out


def choose(shapes, n_families):
    c, f = shapes['category_cards'], shapes['family_pages']
    if n_families and c['coverage'] >= CARD_MIN_COVERAGE and c['contradictions'] <= CARD_MAX_CONTRADICTIONS:
        return 'category_cards', (f'category cards name the family of {c["coverage"]:.0%} of sampled product pages '
                                  f'({c["contradictions"]:.0%} contradictions)')
    if f['coverage'] >= FAMILY_PAGE_MIN:
        return 'family_pages', f'{f["coverage"]:.0%} of sampled product pages list several part numbers'
    m = shapes.get('model_pages', {'coverage': 0})
    if m['coverage'] >= FAMILY_PAGE_MIN:
        return 'model_pages', (f'{m["coverage"]:.0%} of sampled product pages are one model each; each page is its own family '
                               'unless rules R1-R4 join them')
    return 'part_number_rules', 'no shape explains most pages; grouping rules R1-R4 decide, doubtful pairs go to unsure'


def _soup(runner, url):
    facts = runner.links.pages.get(url)
    if facts and facts.html_snapshot and Path(facts.html_snapshot).exists():
        body = Path(facts.html_snapshot).read_bytes()
    else:
        r = runner.fetcher.get(url, kind='html', purpose='page')
        if runner.fetcher.response_blocked(r) or not r.ok or 'html' not in (r.content_type or 'text/html'):
            return None
        body = r.body
    return P.soup_of(body.decode('utf-8', errors='replace'))


def _spread(urls, k):
    urls = sorted(urls)
    if len(urls) <= k:
        return urls
    step = len(urls) / k
    return [urls[int(i * step)] for i in range(k)]


def build_profile(runner, log=print):
    """runner: a ProcessRun (its link file, snapshots and fetch cache are used; nothing else is crawled)."""
    from .run import listing_with_product_evidence
    if not hasattr(runner, 'l1_links'):
        runner.l1_links = runner.links.links_on()
    pages = [u for u in runner.links.pages if not runner.url_reject(u)]
    templates = sorted(D.build_templates(pages).items(), key=lambda kv: -len(kv[1]))[:MAX_TEMPLATES]
    sample, reads = {}, 0
    for key, urls in templates:
        for u in _spread(urls, SAMPLE_PER_TEMPLATE):
            s = _soup(runner, u)
            reads += 1
            if s is not None:
                sample[u] = (key, s)
    spec = learn_card_spec([(u, s) for u, (_, s) in sample.items()])
    card_templates, cards = [], []
    if spec:
        for key, urls in templates:
            got = [u for u, (k, s) in sample.items() if k == key]
            with_cards = [u for u in got if len(extract_cards(sample[u][1], u, spec)) >= MIN_CARDS]
            if got and len(with_cards) / len(got) >= CARD_TEMPLATE_SHARE:
                card_templates.append(key)
                for u in urls[:MAX_CARD_PAGES]:
                    s = sample[u][1] if u in sample else _soup(runner, u)
                    reads += u not in sample
                    if s is not None:
                        cards += extract_cards(s, u, spec)
    families = card_families(cards)
    card_pages = {u for key, urls in templates if key in card_templates for u in urls}
    prod_urls = _spread([u for key, urls in templates if key not in card_templates for u in urls], PRODUCT_SAMPLE)
    products = []
    for u in prod_urls:
        rec, err, _ = runner.load_page(u)
        reads += 1
        if rec and (rec._score >= PRODUCT_SCORE_THRESHOLD or listing_with_product_evidence(rec._signals, PRODUCT_SCORE_THRESHOLD)):
            products.append(rec)
    site_idents = {P.path_tail(u).upper() for u in pages if G.is_identifier(P.path_tail(u))}
    shapes = score_shapes(products, families, site_idents)
    chosen, reason = choose(shapes, len(families))
    log(f'[{runner.site}] profile: {chosen} ({reason}); {reads} pages read, {len(families)} card families')
    return {
        'site': runner.site, 'profile_version': PROFILE_VERSION, 'created_at': now_iso(),
        'family_shape': chosen, 'reason': reason,
        'summary': {'category_cards': 'a family is a card name on a category page; its members are the part numbers on those cards',
                    'family_pages': 'a family is one product page; its variants are the part numbers it lists',
                    'model_pages': 'a family is one product page for one model; rules R1-R4 join pages only on strong evidence',
                    'part_number_rules': 'families are built from part-number pages by rules R1-R4'}[chosen],
        'sample': {'pages_read': reads, 'templates': [k for k, _ in templates], 'card_templates': card_templates,
                   'card_pages': len(card_pages), 'product_pages_scored': len(products)},
        'shapes': shapes, 'card_spec': spec,
        'families': families if chosen == 'category_cards' else [],
    }


def write_profile(profile, out_dir):
    p = Path(out_dir) / f'{profile["site"]}.profile.json'
    p.write_text(json.dumps(profile, indent=1, ensure_ascii=False))
    return p


def profile_assignments(profile, recs):
    """-> ({rec index: family index}, {family index: evidence}) for pages the profile places; others are left to rules."""
    if not profile or profile.get('family_shape') != 'category_cards':
        return {}, {}
    of = {}
    for i, f in enumerate(profile['families']):
        for m in f['members']:
            of.setdefault(m, i)
    fixed, ev = {}, {}
    for i, r in enumerate(recs):
        ident = G.identifier_of(r)
        tail = P.path_tail(r.url).upper()
        k = of.get(ident) if ident in of else of.get(tail)
        if k is not None:
            fixed[i] = k
            f = profile['families'][k]
            ev[k] = f'P1 site profile: category card "{f["name"]}" on {f["source_pages"][0]} lists its part numbers'
    return fixed, ev
