"""End-to-end run for one site -> SiteRun JSON (harness schema) + evidence + flat CSV."""
import collections
import csv
import datetime as dt
import json
import re
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote, urlsplit

from . import assets as A
from . import discover as D
from . import page as P
from . import hosts as H
from . import specs as S
from . import variants as V
from .fetch import Fetcher
from .pdfcache import ParsedPdfCache
from .settings import (AGENT_NAME, AGENT_VERSION, CHROME_MIN_PAGES, CHROME_SHARE, MAX_IMAGES_PER_FAMILY,
                       MAX_PDFS_PER_FAMILY, N, PHASH_SAME_IMAGE, RUNS_DIR, site_config)

SPEC_SHEET = {'spec_sheet', 'submittal'}
KIND_RANK = {'sheet': 0, 'page': 1, 'otherpdf': 2}


def now_iso():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


# ------------------------------------------------------------------ evidence

class Evidence:
    def __init__(self, root):
        self.root = Path(root)
        (self.root / 'files').mkdir(parents=True, exist_ok=True)
        (self.root / 'text').mkdir(parents=True, exist_ok=True)
        self.manifest = {}

    def save(self, url, sha, ext, body, text, content_type, retrieved_at):
        if not sha:
            return
        f = self.root / 'files' / f'{sha}.{ext}'
        if not f.exists():
            f.write_bytes(body)
        if text is not None:   # always rewrite: the text must match the extractor that produced the quotes
            (self.root / 'text' / f'{sha}.txt').write_text(text)
        self.manifest[sha] = (url, sha, len(body), content_type, retrieved_at)

    def write_manifest(self):
        with open(self.root / 'manifest.csv', 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['url', 'sha256', 'bytes', 'content_type', 'retrieved_at'])
            w.writerows(self.manifest.values())


# ------------------------------------------------------------------ page records

@dataclass
class PageRec:
    url: str
    name: str
    crumbs: list
    lang: str
    alternates: dict
    pairs: list
    doc_links: list                 # (url, text)
    image_cands: list
    iframes: list
    price: dict
    skus: list
    sha: str
    tables: list
    text: str
    retrieved_at: str
    flags: list = field(default_factory=list)


SIZE_TOKEN = re.compile(r'(\b\d+(?:[-\s]\d+/\d+)?(?:/\d+)?(?:\.\d+)?\s*(?:"|”|in\b|inch(?:es)?\b|mm\b)'
                        r'|\b\d+(?:\.\d+)?\s?x\s?\d+(?:\.\d+)?(?:\s?x\s?\d+(?:\.\d+)?)?\b'
                        r'|\bDN\s?\d+\b|\bNPS\s?\d+(?:[-/]\d+)*\b)', re.I)
PRODUCT_TYPES = ['triple offset butterfly valve', 'butterfly valve', 'knife gate valve', 'gate valve', 'globe valve',
                 'ball valve', 'check valve', 'plug valve', 'balancing valve', 'pressure reducing valve',
                 'relief valve', 'control valve', 'mixing valve', 'backflow preventer', 'strainer', 'actuator',
                 'positioner', 'coupling', 'adapter', 'fitting', 'elbow', 'tee', 'union', 'nipple', 'hose',
                 'floor sink', 'floor drain', 'trench drain', 'drain', 'clamp', 'hanger', 'bracket', 'outlet box',
                 'box', 'water hammer arrester', 'arrester', 'cleanout', 'interceptor', 'valve']


def fetch_page(fetcher, url, log):
    """Fetch a product page, switching to its English alternate when the page itself is not English."""
    r = fetcher.get(url)
    if not r.ok or ('html' not in (r.content_type or 'text/html')):
        return None, f'fetch failed ({r.status or r.error}): {url}'
    soup = P.soup_of(r.text())
    lang = P.html_lang(soup)
    alts = P.hreflang_alternates(soup, r.final_url)
    if lang and not lang.startswith('en'):
        en = alts.get('en-us') or alts.get('en-ca') or alts.get('en') or next((v for k, v in alts.items() if k.startswith('en')), None)
        if not en:
            return None, f'no English version: {url}'
        r = fetcher.get(en)
        if not r.ok:
            return None, f'English alternate failed: {en}'
        soup = P.soup_of(r.text())
        lang = P.html_lang(soup)
        alts = P.hreflang_alternates(soup, r.final_url)
    return page_rec_from_soup(soup, r.final_url, r.sha256, r.body, lang, alts), None


def page_rec_from_soup(soup, final_url, sha, body, lang=None, alts=None):
    """PageRec from parsed HTML (a fetched page, or an L1 html_snapshot)."""
    lang = lang if lang is not None else P.html_lang(soup)
    alts = alts if alts is not None else P.hreflang_alternates(soup, final_url)

    text = P.visible_text(soup)
    rec = PageRec(
        url=final_url, name=P.product_name(soup), crumbs=P.breadcrumbs(soup), lang=lang or 'en', alternates=alts,
        pairs=P.label_value_pairs(soup),
        doc_links=[(u, t) for u, t in P.links(soup, final_url)
                   if A.DOC_EXT.search(u) or A.cad_from_url(u) or re.search(r'\.zip(\?|$)', u, re.I)],
        image_cands=P.image_candidates(soup, final_url), iframes=P.iframes(soup, final_url),
        price=P.price_signals(soup, text), skus=P.product_skus(soup), sha=sha, tables=P.table_rows(soup), text=text,
        retrieved_at=now_iso())
    rec._body = body  # kept for evidence
    rec._final_host = urlsplit(final_url).hostname or ''
    rec._viewer_links = [u for u, _ in P.links(soup, final_url)]
    return rec


# ------------------------------------------------------------------ families

def base_name(name):
    b = SIZE_TOKEN.sub(' ', name)
    b = re.sub(r'\s*[-–,]\s*$', '', re.sub(r'\s+', ' ', b)).strip(' -–,')
    return b.lower()


def series_code_of(name, url):
    m = re.search(r'\b(?:series|fig(?:ure)?\.?|model|style)\s*([A-Z0-9][\w/\-]*)', name, re.I)
    if m:
        return m.group(1).upper()
    tail = unquote(P.path_tail(url))
    if re.fullmatch(r'[A-Za-z0-9][\w\-]{1,20}', tail) and re.search(r'\d', tail) and tail.count('-') <= 2:
        return tail.upper()
    m = re.search(r'\b([A-Z]*\d[\w\-]*)\b', name)
    return m.group(1).upper() if m else None


def product_type_of(name, crumbs, url=''):
    url_words = unquote(urlsplit(url).path).lower().replace('-', ' ').replace('/', ' ')
    for hay in (name.lower(), ' '.join(crumbs).lower(), url_words):
        for t in PRODUCT_TYPES:
            if re.search(r'\b' + re.escape(t) + r's?\b', hay):
                return t
    return crumbs[-2].lower() if len(crumbs) >= 2 else None


def family_price_page(pages):
    """The page whose price status a variant-less family reports: the first with a published status, else the main page."""
    return next((r for r in pages if r.price['availability'] != 'not_published'), pages[0])


def accessory_families(families):
    """SPEC 3: models listed on an accessory page that are variants of another family are not its variants.

    A family whose identifiers are a strict subset of another family's identifiers loses them; its price status
    moves to family_prices (SPEC 7). Returns the families changed."""
    sets = [{N.norm_token(v['sku']) for v in f.get('variants') or []} for f in families]
    changed = []
    for f, mine in zip(families, sets):
        if mine and any(mine < other for other in sets):
            prices = [p for v in f['variants'] for p in v.get('prices') or []]
            status = next((p for p in prices if p['availability'] != 'not_published'), prices[0] if prices else None)
            f['variants'] = []
            if status:
                f['family_prices'] = [status]
            changed.append(f)
    return changed


def group_families(recs):
    """Pages that differ only by size tokens under the same parent category form one family."""
    groups = collections.OrderedDict()
    for r in recs:
        parent = r.crumbs[-2].lower() if len(r.crumbs) >= 2 else ''
        bn = base_name(r.name)
        key = (parent, bn) if len(bn.split()) >= 2 and SIZE_TOKEN.search(r.name) else ('__page__', r.url)
        groups.setdefault(key, []).append(r)
    return list(groups.values())


GENERIC_NAME_WORDS = {'valve', 'valves', 'series', 'the', 'and', 'with', 'for', 'body', 'ball', 'butterfly', 'gate',
                      'check', 'type', 'style', 'model', 'new', 'design', 'full', 'port', 'standard'}


def pdf_about_family(text, fam, pages):
    """A PDF supplies spec values only if it names this family: its series code, or most of the
    distinctive words of its name. Catalogs and manuals covering other series are listed, not mined."""
    flat = re.sub(r'[\s\-_/.]+', '', text.lower())
    codes = set()
    for c in [fam.get('series_code')] + [P.path_tail(r.url) for r in pages]:
        parts = re.split(r'[-_ ]', (c or '').lower())
        # "92/93-XT" also matches as "92/93"; drop trailing suffix tokens while digits remain
        for n in range(len(parts), 0, -1):
            codes.add(''.join(parts[:n]).replace('/', '').replace('.', ''))
    if any(len(c) >= 2 and re.search(r'\d', c) and c in flat for c in codes):
        return True
    name_words = re.findall(r'[a-z][a-z0-9]{2,}', (fam.get('name') or '').lower())
    url_words = [w for r in pages for w in re.findall(r'[a-z][a-z0-9]{2,}', P.path_tail(r.url).lower())]
    words = [w for w in dict.fromkeys(name_words + url_words) if w not in GENERIC_NAME_WORDS]
    low = text.lower()
    return bool(words) and sum(w in low for w in words) / len(words) >= 0.6


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')[:80] or 'family'


# ------------------------------------------------------------------ spec merge

def _spec_source(kind, url, quote, sha, retrieved_at, page=None, section=None):
    return {'url': url, 'type': 'pdf' if kind != 'page' else 'page', 'page': page, 'section': section,
            'quote': quote[:300] if quote else None, 'snapshot_sha256': sha, 'retrieved_at': retrieved_at}


def merge_field(fname, cands):
    """cands: [{'kind','value','unit','conditions','raw','source'}] -> spec_value per SPEC 6a, or None."""
    if not cands:
        return None
    cands = sorted(cands, key=lambda c: KIND_RANK[c['kind']])
    kind_set = {c['kind'] for c in cands}
    # Collapse candidates of the same kind: union for list fields, first otherwise.
    by_kind = collections.OrderedDict()
    for c in cands:
        k = c['kind']
        if k not in by_kind:
            by_kind[k] = dict(c, sources=[c['source']])
        else:
            cur = by_kind[k]
            if isinstance(cur['value'], list) and isinstance(c['value'], list):
                cur['value'] = list(dict.fromkeys(cur['value'] + c['value']))
                cur['sources'].append(c['source'])
    kinds = list(by_kind)
    disp = by_kind[kinds[0]]
    spec = {'value': disp['value'], 'unit': disp.get('unit'), 'raw_text': (disp.get('raw') or '')[:300] or None,
            'conditions': disp.get('conditions'), 'display_source': 'page' if disp['kind'] == 'page' else 'pdf',
            'sources': list(disp['sources']), 'alt_values': []}
    refined = contradicted = False
    for k in kinds[1:]:
        other = by_kind[k]
        dv, ov = {'value': disp['value'], 'unit': disp.get('unit')}, {'value': other['value'], 'unit': other.get('unit')}
        if N.compare_spec(fname, dv, ov) >= 0.999:
            spec['sources'] += other['sources']
            continue
        spec['alt_values'].append({'value': other['value'], 'unit': other.get('unit'),
                                   'raw_text': (other.get('raw') or '')[:300] or None, 'sources': other['sources']})
        # SPEC 6a: a spec sheet that is a more specific form of the page value is a refinement, not a conflict.
        if disp['kind'] == 'sheet' and k == 'page' and N.refines(fname, dv, ov):
            refined = True
        else:
            contradicted = True
    has_pdf = bool(kind_set & {'sheet', 'otherpdf'})
    has_page = 'page' in kind_set
    if has_pdf and has_page:
        spec['cross_check'] = 'conflict' if contradicted else 'refines' if refined else 'agree'
    else:
        # SPEC 6a conflicts are page vs PDF. PDF-vs-PDF disagreement keeps the spec-sheet value
        # (already displayed by precedence) and is reported via spec['_pdf_disagreement'].
        spec['cross_check'] = 'pdf_only' if has_pdf else 'page_only'
        if spec['alt_values']:
            spec['_pdf_disagreement'] = True
            spec['alt_values'] = []
    if not spec['alt_values']:
        del spec['alt_values']
    return spec


def page_candidates(rec):
    out, extra = collections.defaultdict(list), {}
    for p in rec.pairs:
        if p.field == '_other':
            extra.setdefault(p.label, p.value)
            continue
        fields = [p.field] + (['sizes_available'] if p.field == 'size_range' else [])
        for f in fields:
            parsed = S.parse_field(f, p.value)
            if not parsed:
                continue
            value, unit, cond = parsed
            quote = p.value.split('\n')[0].strip()
            src = _spec_source('page', rec.url, quote, rec.sha, rec.retrieved_at, section=p.label)
            out[f].append({'kind': 'page', 'value': value, 'unit': unit, 'conditions': cond, 'raw': p.value, 'source': src})
            if f == 'size_range' and unit:
                out['size_unit'].append({'kind': 'page', 'value': unit, 'unit': None, 'conditions': None, 'raw': p.value, 'source': src})
        for f, table in (('end_connections', S.CONNECTION_WORDS), ('applications', S.APPLICATION_WORDS)):
            if p.field == f:
                _, unmapped = S.map_vocab(p.value, table)
                if unmapped:
                    extra.setdefault(f + '_other', ', '.join(unmapped)[:300])
    return out, extra


def pdf_candidates(doc, kind):
    out = collections.defaultdict(list)
    texts = doc['_page_texts']

    def page_of(line):
        for i, t in enumerate(texts, 1):
            if line in t:
                return i
        return 1
    for label, value, f, line in S.pairs_from_text(doc['_text']):
        if f == '_other':
            continue
        for fld in [f] + (['sizes_available'] if f == 'size_range' else []):
            parsed = S.parse_field(fld, value)
            if parsed:
                v, unit, cond = parsed
                src = _spec_source(kind, doc['url'], line, doc['sha256'], doc['_retrieved_at'], page=page_of(line), section=label)
                out[fld].append({'kind': kind, 'value': v, 'unit': unit, 'conditions': cond, 'raw': value, 'source': src})
                if fld == 'size_range' and unit:
                    out['size_unit'].append({'kind': kind, 'value': unit, 'unit': None, 'conditions': None, 'raw': value, 'source': src})
    for pg, cells in doc.get('_tables', []):
        if len(cells) > 3:
            continue           # multi-column (per-size) tables are not family-level values
        f = S.field_for_label(cells[0])
        if not f or f == '_other':
            continue
        line = ' | '.join(cells)
        for fld in [f] + (['sizes_available'] if f == 'size_range' else []):
            parsed = S.parse_field(fld, cells[1])
            if parsed:
                v, unit, cond = parsed
                out[fld].append({'kind': kind, 'value': v, 'unit': unit, 'conditions': cond, 'raw': cells[1],
                                 'source': _spec_source(kind, doc['url'], line, doc['sha256'], doc['_retrieved_at'],
                                                        page=pg, section=cells[0])})
    if kind == 'sheet' and 'applications' not in out:
        found = S.applications_from_text(doc['_text'])
        if found:
            terms, quote = found
            out['applications'].append({'kind': kind, 'value': terms, 'unit': None, 'conditions': None, 'raw': quote,
                                        'source': _spec_source(kind, doc['url'], quote, doc['sha256'], doc['_retrieved_at'],
                                                               page=page_of(quote), section='applications')})
    if kind == 'sheet' and 'temperature_range' not in out:
        for line in doc['_text'].splitlines():
            found = S.temperature_from_unit_label(line)
            if found:
                v, unit, quote = found
                out['temperature_range'].append({'kind': kind, 'value': v, 'unit': unit, 'conditions': None, 'raw': quote,
                                                 'source': _spec_source(kind, doc['url'], quote, doc['sha256'], doc['_retrieved_at'],
                                                                        page=page_of(quote), section='temperature rating')})
                break
    if kind == 'sheet' and 'sizes_available' not in out:
        found = S.sizes_from_tables(doc.get('_tables', []))
        if found:
            sizes, unit, pg, quote = found
            src = _spec_source(kind, doc['url'], quote, doc['sha256'], doc['_retrieved_at'], page=pg, section='size table')
            vals = sorted(sizes, key=N.parse_size)
            rng = {'min': vals[0], 'max': vals[-1]}
            out['sizes_available'].append({'kind': kind, 'value': sizes, 'unit': unit, 'conditions': None, 'raw': quote, 'source': src})
            if 'size_range' not in out:
                out['size_range'].append({'kind': kind, 'value': rng, 'unit': unit, 'conditions': None, 'raw': quote, 'source': src})
                if unit:
                    out['size_unit'].append({'kind': kind, 'value': unit, 'unit': None, 'conditions': None, 'raw': quote, 'source': src})
    if kind == 'sheet':
        for f, hits in S.scan_text_for_lists(doc['_text']).items():
            if f in out:
                continue
            values = list(dict.fromkeys(v for vals, _ in hits for v in vals))
            v0, line0 = hits[0]
            out[f].append({'kind': kind, 'value': values, 'unit': None, 'conditions': None, 'raw': line0,
                           'source': _spec_source(kind, doc['url'], line0, doc['sha256'], doc['_retrieved_at'],
                                                  page=page_of(line0))})
    return out


# ------------------------------------------------------------------ main run

class SiteRun:
    def __init__(self, site, limit=None, only_urls=None, refresh=False, log=print, out_dir=None,
                 input_url=None, use_config_hosts=False):
        self.site, self.limit, self.only_urls, self.log = site, limit, only_urls, log
        self.cfg = site_config(site, input_url)
        self.config_hosts = self.cfg.get('allowed_hosts')
        self.use_config_hosts = use_config_hosts and bool(self.config_hosts)
        # Pages come only from the manufacturer's own domain; asset hosts are detected after pages are read.
        self.page_hosts = H.page_hosts(self.cfg['input_url'])
        self.allowed = list(self.config_hosts) if self.use_config_hosts else list(self.page_hosts)
        self.viewer_hosts = self.cfg['cad_viewer_hosts']
        self.fetcher = Fetcher(site, refresh=refresh, log=log)
        self.out_dir = Path(out_dir or RUNS_DIR)
        self.evidence = Evidence(self.out_dir / f'{site}.evidence')
        self.pdf_cache = ParsedPdfCache()
        self.flags = collections.Counter()
        self.flag_examples = {}

    def flag(self, key, example=None):
        self.flags[key] += 1
        if example and key not in self.flag_examples:
            self.flag_examples[key] = example

    def guarded(self, flag_key, url, fn, *args):
        """Run one page/family step; a crash is flagged with its URL and must not kill the site run."""
        try:
            return fn(*args)
        except Exception as e:   # noqa: BLE001  (any bug in one page is isolated)
            self.flag(flag_key, f'{url}: {type(e).__name__}: {e}')
            self.log(f'  CRASH {flag_key} {url}: {type(e).__name__}: {e}')
            self.log(traceback.format_exc(limit=6))
            return None

    # -------------------------------------------------- discovery
    def discover(self):
        base = self.cfg['input_url']
        home = self.fetcher.get(base)
        profile = {'fetch_mode': 'http', 'blocked': False}
        if not home.ok:
            profile['blocked'] = home.status in (401, 403, 429)
            self.flag('blocked_by_site' if profile['blocked'] else 'homepage_fetch_failed', f'{home.status} {home.error or ""}'.strip())
        html = home.text() if home.ok else ''
        profile['platform'] = next((name for name, pat in [
            ('WordPress', r'wp-content|wp-includes'), ('Drupal', r'/sites/default/files|drupal'),
            ('Sitefinity', r'sitefinity|/docs/default-source'), ('BigCommerce', r'bigcommerce'),
            ('Shopify', r'cdn\.shopify|shopify'), ('Magento', r'magento|mage/'), ('ASP.NET', r'__VIEWSTATE|aspnet')]
            if re.search(pat, html, re.I)), 'unknown')
        urls, lastmod, sitemaps = D.sitemap_urls(self.fetcher, base, self.log)
        profile['sitemaps'] = sitemaps
        from_sitemap = D.candidate_pages(urls, self.page_hosts)
        from_crawl = D.crawl_navigation(self.fetcher, base, self.page_hosts, log=self.log)
        sm_keys = {N.match_key(u) for u in from_sitemap}
        cr_keys = {N.match_key(u) for u in from_crawl}
        cands = list(dict.fromkeys(from_sitemap + [u for u in from_crawl if N.match_key(u) not in sm_keys]))
        profile['discovery'] = {'sitemap_pages': len(sm_keys), 'crawl_pages': len(cr_keys),
                                'both': len(sm_keys & cr_keys), 'crawl_only': len(cr_keys - sm_keys)}
        templates = D.build_templates(cands)
        cls = D.classify_templates(self.fetcher, templates, self.log)
        product_templates = [k for k, v in cls.items() if v['product']]
        product_urls = sorted({u for k in product_templates for u in templates[k]})
        profile['templates'] = {k: {kk: vv for kk, vv in v.items() if kk != 'samples'} for k, v in cls.items()}
        profile['product_templates'] = product_templates
        profile['product_urls_total'] = len(product_urls)
        self.sample_pages = [s['url'] for v in cls.values() for s in v['samples']]
        self.lastmod = lastmod
        return profile, product_urls

    # -------------------------------------------------- chrome detection
    def chrome_keys(self, recs):
        """Asset keys that appear on too many pages to be product-specific."""
        pages = list(recs)
        for u in self.sample_pages:
            if u not in {r.url for r in recs}:
                rec, _ = fetch_page(self.fetcher, u, self.log)   # cached from template sampling
                if rec:
                    pages.append(rec)
        n = len(pages)
        counts = collections.Counter()
        for r in pages:
            keys = {N.match_key(u, drop_asset_params=True) for u, _ in r.doc_links}
            keys |= {N.image_key(c[0]) for c in r.image_cands}
            counts.update(keys)
        if n < CHROME_MIN_PAGES:
            return set(), n
        return {k for k, c in counts.items() if c / n > CHROME_SHARE and c >= 3}, n

    # -------------------------------------------------- documents & CAD
    def process_docs(self, fam_pages, chrome):
        docs, cads, seen = [], [], set()
        links = []
        for r in fam_pages:
            for u, t in r.doc_links:
                links.append((u, t, r.url))
            for u in r.iframes + r._viewer_links:
                if N.host_allowed(u, self.viewer_hosts) and u not in seen:
                    seen.add(u)
                    cads.append({'url': u, 'cad_type': 'cad_viewer', 'formats': [], 'gated': True, 'found_on': r.url,
                                 'variant_skus': []})
        # Primary-looking documents first so the per-family cap keeps them.
        links.sort(key=lambda x: 0 if A.classify_doc(x[0], x[1]) in A.PRIMARY else 1)
        n_pdf = 0
        for u, text, found_on in links:
            key = N.match_key(u, drop_asset_params=True)
            if key in seen or key in chrome:
                if key in chrome:
                    self.flag('site_chrome_document_skipped', u)
                continue
            seen.add(key)
            if not N.host_allowed(u, self.allowed):
                self.flag('off_allowlist_link_skipped', u)
                continue
            cad = A.cad_from_url(u)
            if cad:
                cads.append({'url': u, **cad, 'gated': False, 'found_on': found_on, 'variant_skus': []})
                continue
            if re.search(r'\.zip(\?|$)', u, re.I):
                if A.zip_name_suggests_cad(u, text):
                    cads.append(self.zip_cad(u, text, found_on))
                continue
            if n_pdf >= MAX_PDFS_PER_FAMILY:
                self.flag('pdf_cap_reached', found_on)
                continue
            n_pdf += 1
            d = self.process_pdf(u, text, found_on)
            if d:
                docs.append(d)
        return docs, [c for c in cads if c]

    def zip_cad(self, url, text, found_on):
        fmts_guess = sorted({f for k, f in A.CAD_EXT.items() if re.search(r'\b' + k + r'\b', unquote(url).lower() + ' ' + text.lower())}) or []
        r = self.fetcher.get(url, kind='zip')
        if r.blocked_by_robots:
            self.flag('robots_blocked_cad', url)
            return {'url': url, 'cad_type': 'cad_file', 'formats': fmts_guess, 'gated': False, 'found_on': found_on, 'variant_skus': []}
        if not r.ok:
            self.flag('cad_download_failed', url)
            return None
        fmts = A.zip_cad_formats(r.body)
        if not fmts:
            return None   # a zip without CAD files (software, docs) is not CAD
        ctype = 'bim' if set(fmts) <= A.BIM_FORMATS else 'cad_file'
        return {'url': url, 'cad_type': ctype, 'formats': fmts, 'gated': False, 'found_on': found_on, 'variant_skus': []}

    def process_pdf(self, url, link_text, found_on):
        d = {'url': url, 'doc_type': None, 'priority': None, 'lang': None, 'title': link_text or None,
             'revision_date': None, 'sha256': None, 'bytes': None, 'http_status': None, 'mime_verified': False,
             'found_on': found_on, 'variant_skus': []}
        r = self.fetcher.get(url, kind='pdf')
        if r.blocked_by_robots:
            self.flag('robots_blocked_pdf', url)
            d['doc_type'] = A.classify_doc(url, link_text)
            d['lang'], _ = A.detect_lang('', url)
        elif not r.ok:
            d['http_status'] = r.status
            self.flag('pdf_fetch_failed', f'{r.status or r.error}: {url}')
            return None
        else:
            d['http_status'] = r.status
            d['bytes'] = len(r.body)
            if not A.is_pdf(r.body):
                self.flag('linked_document_not_pdf', url)
                d['doc_type'] = A.classify_doc(url, link_text)
                d['lang'], _ = A.detect_lang('', url)
            else:
                text, pages, title, rev, table_rows = self.pdf_cache.get(r.sha256, r.body)
                d.update(sha256=r.sha256, mime_verified=True, title=title or link_text or None, revision_date=rev)
                d['lang'], assumed = A.detect_lang(text, url)
                if assumed:
                    self.flag('pdf_language_assumed_from_filename', url)
                d['doc_type'] = A.classify_doc(url, link_text, title, pages[0] if pages else '')
                ts = now_iso()
                self.evidence.save(url, r.sha256, 'pdf', r.body, text, 'application/pdf', ts)
                d['_text'], d['_page_texts'], d['_retrieved_at'], d['_tables'] = text, pages, ts, table_rows
        if not (d['lang'] or 'en').split('+')[0].startswith('en'):
            self.flag('non_english_document_excluded', url)
            return None
        d['priority'] = 'primary' if d['doc_type'] in A.PRIMARY else 'secondary'
        return d

    # -------------------------------------------------- images
    def process_images(self, fam_pages, chrome, family_counts):
        groups = collections.OrderedDict()
        for r in fam_pages:
            for url, width, alt, ctx in r.image_cands:
                if not N.host_allowed(url, self.allowed):
                    continue
                if not (A.IMAGE_EXT.search(url) or ctx in ('srcset', 'jsonld')):
                    continue
                name = unquote(urlsplit(url).path.rsplit('/', 1)[-1])
                if A.CHROME_IMAGE.search(name) or A.CHROME_IMAGE.search(alt or ''):
                    continue
                if A.NON_PRODUCT_PHOTO.search(name) or A.NON_PRODUCT_PHOTO.search(alt or ''):
                    self.flag('installation_or_lifestyle_photo_skipped', url)
                    continue
                key = N.image_key(url)
                if key in chrome or family_counts.get(key, 0) >= 3:
                    continue
                groups.setdefault(key, {'cands': [], 'alt': alt, 'found_on': r.url})['cands'].append((url, width))
        images = []
        for key, g in list(groups.items())[:MAX_IMAGES_PER_FAMILY * 2]:
            if len(images) >= MAX_IMAGES_PER_FAMILY:
                break
            ranked = sorted(dict.fromkeys(g['cands']), key=lambda c: A.rank_candidate(*c), reverse=True)
            tries = [u for u, _ in ranked]
            if A.SIZE_MARK.search(tries[0]):
                tries = A.original_candidates(tries[0]) + tries
            got = None
            for u in list(dict.fromkeys(tries))[:4]:
                resp = self.fetcher.get(u, kind='image')
                if not resp.ok or not resp.content_type.startswith('image'):
                    continue
                w, h, ph = A.image_dims_phash(resp.body)
                if w and h:
                    got = (u, w, h, ph)
                    break
            if not got:
                continue
            u, w, h, ph = got
            if min(w, h) < 300:
                self.flag('image_below_300px_skipped', u)
                continue
            dup = next((im for im in images if N.phash_distance(im['phash'], ph) is not None
                        and N.phash_distance(im['phash'], ph) <= PHASH_SAME_IMAGE), None)
            if dup:
                if w * h > dup['width'] * dup['height']:
                    dup.update(url=u, width=w, height=h, phash=ph)
                continue
            images.append({'url': u, 'image_type': A.image_type_of(u, g['alt']), 'width': w, 'height': h,
                           'phash': ph, 'found_on': g['found_on']})
        return images

    # -------------------------------------------------- family assembly
    def build_family(self, pages, chrome, family_counts):
        main = pages[0]
        fid = slug(P.path_tail(main.url) or main.name)
        fam = {'family_id': fid, 'name': main.name if len(pages) == 1 else base_name(main.name).title() or main.name,
               'series_code': series_code_of(main.name, main.url),
               'product_type': product_type_of(main.name, main.crumbs, main.url), 'canonical_url': main.url,
               'alternates': [{'url': u, 'locale': k} for k, u in sorted(main.alternates.items())
                              if not k.startswith('en') and k != 'x-default'],
               'market_flag': 'na' if main.lang in ('en', 'en-us', 'en-ca', '') else 'non_na'}
        docs, cads = self.process_docs(pages, chrome)
        fam['images'] = self.process_images(pages, chrome, family_counts)

        # specs: page candidates + spec-sheet candidates + other-PDF candidates
        cands, extra = collections.defaultdict(list), {}
        for r in pages:
            c, e = page_candidates(r)
            extra.update(e)
            for f, lst in c.items():
                cands[f] += lst
        family_docs = []
        for d in docs:
            if d.get('_text'):
                if not pdf_about_family(d['_text'], fam, pages):
                    self.flag('pdf_not_about_family_not_used_for_specs', f'{main.url} <- {d["url"]}')
                    continue
                family_docs.append(d)
                kind = 'sheet' if d['doc_type'] in SPEC_SHEET else 'otherpdf'
                for f, lst in pdf_candidates(d, kind).items():
                    cands[f] += lst
        specs = {}
        for f in N.SPEC_KINDS:
            m = self.merge_spec(f, cands.get(f, []))
            if m:
                if m.pop('_pdf_disagreement', False):
                    self.flag('pdf_vs_pdf_disagreement_kept_spec_sheet', f'{main.url} [{f}]')
                if m['cross_check'] == 'conflict':
                    self.flag('page_vs_pdf_conflict', f'{main.url} [{f}]')
                specs[f] = m
        fam['specs'] = specs
        kinds = {s['type'] for v in specs.values() for s in v['sources'] + [x for a in v.get('alt_values', []) for x in a['sources']]}
        fam['spec_source_summary'] = 'both' if kinds >= {'pdf', 'page'} else 'pdf' if 'pdf' in kinds else 'page' if kinds else 'none'
        if extra:
            fam['additional_specs'] = extra

        # variants + prices
        variants = []
        for r in pages:
            tail = P.path_tail(r.url).upper()
            skus = r.skus or ([tail] if len(pages) > 1 and V._is_id(tail) else [])
            for sku in skus:
                if any(N.norm_token(v['sku']) == N.norm_token(sku) for v in variants):
                    continue
                m = SIZE_TOKEN.search(r.name)
                v = {'sku': sku, 'size': m.group(0).strip() if m else None, 'page_url': r.url, 'prices': [self.page_price(r)]}
                variants.append(v)
        if not variants:
            variants = self.table_variants(pages, family_docs)
        if not variants and V.from_name(pages[0].name):
            variants = [{'sku': sku, 'size': None, 'page_url': pages[0].url, 'prices': [self.page_price(pages[0])]}
                        for sku in V.from_name(pages[0].name)]
            self.flag('variants_from_heading_list', pages[0].url)
        fam['variants'] = variants
        if not variants:   # SPEC 7: a family without identifiers carries its price status itself, always filled
            fam['family_prices'] = [self.page_price(family_price_page(pages))]

        fam['documents'] = [{k: v for k, v in d.items() if not k.startswith('_')} for d in docs]
        fam['cad'] = cads
        for r in pages:   # page snapshots for evidence (quotes are checked against these)
            self.evidence.save(r.url, r.sha, 'html', r._body, r.text, 'text/html', r.retrieved_at)
        return fam

    def merge_spec(self, fname, cands):
        return merge_field(fname, cands)

    def page_price(self, r):
        pr = dict(r.price)
        price = {'amount': pr.get('amount'), 'currency': pr.get('currency'), 'price_type': 'list' if pr.get('amount') else None,
                 'availability': pr['availability'],
                 'source': {'url': r.url, 'type': 'page', 'page': None, 'quote': pr.get('quote'),
                            'snapshot_sha256': r.sha, 'retrieved_at': r.retrieved_at}}
        if pr['availability'] == 'price_shown' and not pr.get('currency'):
            price['currency'] = 'USD'
            self.flag('price_currency_assumed_usd', r.url)
        return price

    def table_variants(self, pages, family_docs):
        """SPEC 3 variants from model/part-number tables on the family's pages, else its own spec sheets."""
        main = pages[0]
        found = []
        for r in pages:
            found += [(s, z, r) for s, z, _ in V.from_rows(r.tables) + V.from_lines(r.text)]
        if not found:
            for d in family_docs:
                if d['doc_type'] in SPEC_SHEET:
                    found += [(s, z, main) for s, z, _ in V.from_rows([c for _, c in d.get('_tables', [])]) + V.from_lines(d['_text'])]
                    if found:
                        break
        out, seen = [], set()
        for sku, size, r in found:
            k = N.norm_token(sku)
            if k in seen:
                continue
            seen.add(k)
            out.append({'sku': sku, 'size': size, 'page_url': r.url, 'prices': [self.page_price(r)]})
        if out:
            self.flag('variants_from_identifier_tables', main.url)
        return out

    # -------------------------------------------------- run
    def run(self):
        started = now_iso()
        self.log(f'[{self.site}] discovering ...')
        profile, product_urls = self.discover()
        targets = self.only_urls or product_urls
        if self.limit and len(targets) > self.limit:
            step = len(targets) / self.limit
            targets = [targets[int(i * step)] for i in range(self.limit)]
        self.log(f'[{self.site}] {len(product_urls)} product URLs; processing {len(targets)}')
        recs = []
        for i, u in enumerate(targets, 1):
            rec, err = self.guarded('page_crashed', u, fetch_page, self.fetcher, u, self.log) or (None, 'crashed')
            if err == 'crashed':
                continue
            if err:
                self.flag('page_skipped', err)
                continue
            if not N.host_allowed(rec.url, self.page_hosts):
                self.flag('product_page_redirects_off_site', f'{u} -> {rec.url}')
                continue
            recs.append(rec)
            if i % 25 == 0:
                self.log(f'  pages {i}/{len(targets)}')
        detected, evidence = H.detect_asset_hosts(recs, self.page_hosts)
        if not self.use_config_hosts:
            self.allowed = list(self.page_hosts) + detected
        cfg_hosts = set(self.config_hosts or [])
        norm = lambda hs: {h.lower().removeprefix('www.') for h in hs}
        self.host_report = {
            'mode': 'config' if self.use_config_hosts else 'auto', 'page_hosts': self.page_hosts,
            'detected_asset_hosts': detected, 'candidate_counts': dict(list(evidence.items())[:15]),
            'config_hosts': sorted(cfg_hosts) or None,
            'config_hosts_not_covered': sorted(h for h in norm(cfg_hosts) if not N.host_allowed('https://' + h + '/', self.allowed)) if cfg_hosts else None,
            'detected_not_in_config': sorted(h for h in detected if cfg_hosts and not N.host_allowed('https://' + h + '/', list(cfg_hosts))) if cfg_hosts else None,
        }
        self.log(f'[{self.site}] hosts: pages={self.page_hosts} assets={detected}')
        chrome, n_chrome_pages = self.chrome_keys(recs)
        self.log(f'[{self.site}] site-chrome assets: {len(chrome)} (from {n_chrome_pages} pages)')
        fam_groups = group_families(recs)
        family_counts = collections.Counter()
        for g in fam_groups:
            family_counts.update({N.image_key(c[0]) for r in g for c in r.image_cands})
        families, ids = [], collections.Counter()
        for i, g in enumerate(fam_groups, 1):
            fam = self.guarded('family_crashed', g[0].url, self.build_family, g, chrome, family_counts)
            if fam is None:
                continue
            ids[fam['family_id']] += 1
            if ids[fam['family_id']] > 1:
                fam['family_id'] += f'-{ids[fam["family_id"]]}'
            families.append(fam)
            self.log(f'  family {i}/{len(fam_groups)} {fam["family_id"]}: specs={len(fam["specs"])} '
                     f'docs={len(fam["documents"])} cad={len(fam["cad"])} images={len(fam["images"])}')
        for fam in accessory_families(families):
            self.flag('accessory_models_not_variants', fam['canonical_url'])
        self.evidence.write_manifest()

        def pct(pred):
            return round(sum(1 for f in families if pred(f)) / len(families), 4) if families else 0.0
        full_run = not self.limit and not self.only_urls
        run = {
            'schema_version': '1.0', 'site': self.site, 'input_url': self.cfg['input_url'], 'run_at': started,
            'agent': {'name': AGENT_NAME, 'version': AGENT_VERSION},
            'site_profile': {**profile, 'hosts': self.host_report},
            'families': families,
            'coverage': {
                'families': len(families),
                'sitemap_families': len(group_families(recs)) if full_run else None,
                'pct_with_specs': pct(lambda f: bool(f['specs'])),
                'pct_with_spec_sheet': pct(lambda f: any(d['doc_type'] in SPEC_SHEET for d in f['documents'])),
                'pct_with_image': pct(lambda f: bool(f['images'])),
                'pct_with_cad': pct(lambda f: bool(f['cad'])),
                'pct_with_price': pct(lambda f: any(p['availability'] == 'price_shown' for v in f['variants'] for p in v['prices'])),
            },
            'unlinked': [],
            'flags': [f'{k}: {v}' + (f' (e.g. {self.flag_examples[k]})' if k in self.flag_examples else '')
                      for k, v in sorted(self.flags.items())],
            'run_stats': {**self.fetcher.stats, 'finished_at': now_iso(), 'limit': self.limit},
        }
        return run


def write_outputs(run, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    site = run['site']
    jp = out_dir / f'{site}.json'
    jp.write_text(json.dumps(run, indent=2, ensure_ascii=False))
    with open(out_dir / f'{site}.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['url', 'url_type', 'family_id'])
        for fam in run['families']:
            w.writerow([fam['canonical_url'], 'site_page', fam['family_id']])
            for d in fam['documents']:
                w.writerow([d['url'], d['doc_type'], fam['family_id']])
            for c in fam['cad']:
                w.writerow([c['url'], c['cad_type'], fam['family_id']])
            for im in fam['images']:
                w.writerow([im['url'], 'image', fam['family_id']])
    return jp
