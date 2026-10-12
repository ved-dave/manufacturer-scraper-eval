"""Approach B processing layer: a Layer 1 link file in; the SPEC SiteRun JSON and <site>.decisions.jsonl out.

Steps (APPROACH_B_RUN.md Phase 3): ingest and tag -> page edges (L1 found_on / html_snapshot, else fetch each
candidate page once) -> page roles -> evidence-based family grouping -> asset decisions by evidence, not location
-> documents / images / specs / prices through the existing extraction code. Every keep / drop / unsure decision
is written with its reason; unsure items carry the context a later resolver (proposal Phase 3) needs.
"""
import collections
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import unquote, urlsplit

from .. import assets as A
from .. import discover as D
from .. import hosts as H
from .. import page as P
from ..pipeline import (GENERIC_NAME_WORDS, SPEC_SHEET, SiteRun, accessory_families, base_name, merge_field, now_iso,
                        page_rec_from_soup, series_code_of, slug, write_outputs)
from ..pdfcache import ParsedPdfCache
from ..settings import (AGENT_NAME, AGENT_VERSION, CACHE_DIR, CHROME_MIN_PAGES, CHROME_SHARE, MAX_IMAGES_PER_FAMILY,
                        MAX_PDFS_PER_FAMILY, N, PHASH_SAME_IMAGE, PRODUCT_SCORE_THRESHOLD)
from . import grouping as G
from . import profile as SP
from .resolve import same_family_links
from .context import canonical_of, link_context
from .fetching import AssetPrefetcher, HostQueueFetcher
from .readers import read_links

RELATED_SECTION = re.compile(r'related|similar|you may also|also like|accessor|recommended (?:products|items|for)|other products|compare|'
                             r'popular|recently viewed|customers also', re.I)
CHART_IMAGE = re.compile(r'chart|graph|curve|(pressure|temp\w*|flow|loss|performance)[\s_-]*diagram', re.I)
DIMENSION_WORDS = re.compile(r'dimension|drawing|\bdims?\b', re.I)
DOC_SHARED_LIMIT = 10     # a document on more families than this that names none of them is not product-specific
IMAGE_SHARED_LIMIT = 2
PROGRESS_EVERY = 200


def _flat(s):
    return re.sub(r'[\s\-_/.%()+,]+', '', (s or '').lower())


def _filename(url):
    return unquote(urlsplit(url).path.rsplit('/', 1)[-1])


LISTING_OVERRIDE_SIGNALS = ('spec_pairs', 'spec_download', 'jsonld_product')


def listing_with_product_evidence(signals, threshold):
    """A listing cue (many same-section links) on a page whose URL names it a product page (url_word), that has strong
    product evidence and would pass the product threshold without that cue: not a clear listing, so it is kept and
    queued as unsure. Category pages with spec-like facet tables have no product URL word and stay dropped."""
    if 'listing_like' not in signals or 'url_word' not in signals or not any(k in signals for k in LISTING_OVERRIDE_SIGNALS):
        return False
    return sum(v for k, v in signals.items() if k != 'listing_like') >= threshold


def apply_spec_table(signals, has_spec_table):
    """L1 has_spec_table: true counts as a spec table; false removes only that signal, not a single spec value seen on the page."""
    if has_spec_table is True:
        signals.pop('spec_pair', None)
        signals['spec_pairs'] = 3
    elif has_spec_table is False:
        signals.pop('spec_pairs', None)


def grouped_variants(fam, pages, price_of):
    """Every page grouped into a family is one of its variants (its part number), so the family's pages and
    provenance stay complete even when the page carries no SKU the variant extractor recognises."""
    have_pages = {v.get('page_url') for v in fam['variants']}
    have_skus = {N.norm_token(v['sku']) for v in fam['variants']}
    for r in pages:
        ident = G.identifier_of(r)
        if r.url in have_pages or not ident or N.norm_token(ident) in have_skus:
            continue
        fam['variants'].append({'sku': ident, 'size': None, 'page_url': r.url, 'prices': [price_of(r)]})
        have_skus.add(N.norm_token(ident))
    if fam['variants']:
        fam.pop('family_prices', None)
    fam['_grouped'] = True


class ProcessRun(SiteRun):
    def __init__(self, site, links_path, level=None, out_dir=None, input_url=None, refresh=False, offline=False,
                 log=print, allowed_hosts=None, fetcher=None, prefetch=True, resolutions=None, profile=None):
        super().__init__(site, refresh=refresh, log=log, out_dir=out_dir, input_url=input_url)
        self.resolved_links = same_family_links(resolutions) if resolutions else []
        self.profile = json.loads(Path(profile).read_text()) if isinstance(profile, (str, Path)) else profile
        self.fetcher = fetcher or HostQueueFetcher(site, cache_name=f'{site}.process', refresh=refresh, log=log,
                                                   offline=offline)
        self.pdf_cache = ParsedPdfCache(root=CACHE_DIR / 'parsed-pdf.process')
        self.links = read_links(links_path, level)
        hosts = allowed_hosts or self.config_hosts
        self.allowed = list(hosts) if hosts else None      # None: detected from the pages after they are read
        self.decisions = []
        self.sample_pages = []
        self.ctx = {}
        self.l1_dims = {}
        self._cur = None
        self.page_sources = collections.Counter()
        self.prefetch = prefetch
        self.img_alias = {}

    # -------------------------------------------------- decisions log
    def decide(self, kind, decision, reason, url=None, **extra):
        d = {'kind': kind, 'decision': decision, 'reason': reason, 'url': url}
        if self._cur and 'family' not in extra:
            d['family_id'] = self._cur['family_id']
        d.update(extra)
        self.decisions.append(d)
        return decision

    def family_ref(self):
        c = self._cur or {}
        return {k: c.get(k) for k in ('family_id', 'name', 'series_code', 'canonical_url', 'identifiers')}

    def unsure(self, unsure_kind, question, candidate, evidence_for, evidence_against, why, default, family=None):
        fam = family if family is not None else self.family_ref()
        key = hashlib.sha256(json.dumps([unsure_kind, question, candidate.get('url'), fam.get('family_id')],
                                        sort_keys=True).encode()).hexdigest()[:16]
        self.decide(unsure_kind, 'unsure', why, url=candidate.get('url'), unsure_kind=unsure_kind, question=question,
                    candidate=candidate, family=fam, evidence_for=evidence_for, evidence_against=evidence_against,
                    why_undecided=why, default_action=default, cache_key=key)
        return 'unsure'

    def last_default_keep(self):
        return self.decisions[-1].get('default_action') == 'keep'

    # -------------------------------------------------- family naming evidence
    def make_ref(self, g):
        main = g[0]
        idents = list(dict.fromkeys([i for i in (G.identifier_of(r) for r in g) if i] + [s for r in g for s in r.skus]))
        stems = list(dict.fromkeys(s for s in (G.stem_of(i) for i in idents) if s))
        series = series_code_of(main.name, main.url)
        if len(g) > 1 and len(stems) == 1 and (not series or series.upper() in idents):
            series = stems[0]
        name = main.name if len(g) == 1 else (base_name(main.name).title() or main.name)
        codes = set()
        for c in [series] + idents + stems:
            f = _flat(c)
            if len(f) >= 3 and re.search(r'\d', f):
                codes.add(f)
        words = [w for w in dict.fromkeys(re.findall(r'[a-z][a-z0-9]{3,}', (name or '').lower()))
                 if w not in GENERIC_NAME_WORDS][:3]
        return {'family_id': slug(P.path_tail(main.url) or main.name), 'name': name, 'series_code': series,
                'canonical_url': main.url, 'identifiers': idents[:50], '_codes': codes, '_words': words}

    _code_res = {}

    @classmethod
    def _code_in(cls, code, text_low, flat=None):
        """The code appears as a whole token run ("778v" in "778v-valve", not in "778vws"; "ab10002" in "AB100-02")."""
        rx = cls._code_res.get(code)
        if rx is None:
            rx = cls._code_res[code] = re.compile(r'(?<![a-z0-9])' + r'[\s\-_./]?'.join(map(re.escape, code)) + r'(?![a-z0-9])')
        return bool(rx.search(text_low))

    def names_family(self, *texts, ref=None):
        ref = ref or self._cur
        if not ref:
            return None
        low = unquote(' '.join(t or '' for t in texts)).lower()
        flat = _flat(low)
        for c in sorted(ref['_codes'], key=len, reverse=True):
            if self._code_in(c, low, flat):
                return (f'names "{c}"', c)
        if len(ref['_words']) >= 2 and all(w in low for w in ref['_words']):
            return (f'names the family ("{" ".join(ref["_words"])}")', '')
        return None

    def names_strongly(self, *texts):
        """names_family, but only by the family's own series code or an identifier (not a shared stem)."""
        hit = self.names_family(*texts)
        if not hit or not hit[1]:
            return None
        own = {_flat(x) for x in self._cur['identifiers'] + [self._cur['series_code'] or '']} - {''}
        return hit if _flat(hit[1]) in own else None

    def names_other(self, *texts):
        """(family_id, code) of the longest code of ANOTHER family named in the texts, if any."""
        if not self._cur or not getattr(self, 'code_index', None):
            return None
        low = unquote(' '.join(t or '' for t in texts)).lower()
        best = None
        for c, fids in self.code_index:
            if self._cur['family_id'] in fids or (best and len(c) <= len(best[1])):
                continue
            if len(c) >= 4 and self._code_in(c, low):
                best = (sorted(fids)[0], c)
        return best

    # -------------------------------------------------- pages
    def url_reject(self, u):
        s = urlsplit(u)
        if not N.host_allowed(u, self.page_hosts):
            return 'off-site page'
        loc = N.locale_of_url(u)
        if not N.is_english(loc):
            return f'language copy (URL locale {loc})'
        if D.LISTING_PARAMS.search(s.query):
            return 'listing / sort / search URL parameters'
        if D.FILE_EXT.search(s.path):
            return 'file URL, not a page'
        if D.NON_PRODUCT_WORDS.search(s.path):
            return 'non-product section by URL'
        return None

    def load_page(self, url):
        """-> (PageRec | None, error | None, blocked)."""
        facts = self.links.pages.get(url)
        if facts and facts.html_snapshot and Path(facts.html_snapshot).exists():
            body, final, source = Path(facts.html_snapshot).read_bytes(), facts.final_url or url, 'snapshot'
        else:
            r = self.fetcher.get(url, kind='html', purpose='page')
            if self.fetcher.response_blocked(r):
                return None, f'blocked ({r.status or r.error})', True
            if not r.ok or 'html' not in (r.content_type or 'text/html'):
                return None, f'fetch failed ({r.status or r.error})', False
            body, final, source = r.body, r.final_url, 'fetched'
        if not N.host_allowed(final, self.page_hosts):
            return None, f'redirects off-site to {final}', False
        html = body.decode('utf-8', errors='replace')
        soup = P.soup_of(html)
        rec = page_rec_from_soup(soup, final, hashlib.sha256(body).hexdigest(), body)
        rec._source = source
        rec._canonical = (facts.canonical_url if facts and facts.canonical_url else None) or canonical_of(soup, final) or final
        score, signals = D.score_product_page(soup, final, html)
        if facts:   # L1 page facts win over what we derive from the HTML
            if facts.breadcrumb:
                rec.crumbs = list(facts.breadcrumb)
            if facts.lang:
                rec.lang = facts.lang
            if facts.hreflang:
                rec.alternates = dict(facts.hreflang)
            if facts.jsonld_product:
                signals['jsonld_product'] = 3
                ld = facts.jsonld_product
                if ld.get('name') and not rec.name:
                    rec.name = str(ld['name'])
                if ld.get('sku') and str(ld['sku']) not in rec.skus:
                    rec.skus = [str(ld['sku'])] + rec.skus
            if facts.h1 and not rec.name:
                rec.name = facts.h1
            apply_spec_table(signals, facts.has_spec_table)
            if facts.n_links_same_section is not None:
                signals.pop('listing_like', None)
                if facts.n_links_same_section > 15:
                    signals['listing_like'] = -4
        if rec.lang and not N.is_english(rec.lang.lower()):
            return None, f'language copy (lang={rec.lang})', False
        rec._signals, rec._score = signals, sum(signals.values())
        ctx = link_context(soup, final)
        for l in self.l1_links.get(url, []) + (self.l1_links.get(final, []) if final != url else []):
            c = ctx.setdefault(l.url, {})
            c.update({k: getattr(l, k) for k in ('link_text', 'section', 'in_chrome', 'link_kind') if getattr(l, k) is not None})
            c['from'] = 'L1'
            if l.url_type == 'image':
                alt = l.alt or ''
                rec.image_cands.append((l.url, l.width, alt, 'img'))
                for s in l.srcset or []:
                    rec.image_cands.append((s['url'], s.get('width'), alt, 'srcset'))
                    self.img_alias[N.image_key(s['url'])] = N.image_key(l.url)
                    ctx.setdefault(s['url'], dict(c))
                if l.wrapping_link:
                    rec.image_cands.append((l.wrapping_link, None, alt, 'link'))
                    self.img_alias[N.image_key(l.wrapping_link)] = N.image_key(l.url)
                    ctx.setdefault(l.wrapping_link, dict(c))
                if l.width and l.height:
                    self.l1_dims[l.url] = (l.width, l.height)
            elif l.url_type == 'page':
                continue
            elif not any(u == l.url for u, _ in rec.doc_links):
                rec.doc_links.append((l.url, l.link_text or ''))
        self.ctx[rec.url] = ctx
        self.page_sources[source] += 1
        return rec, None, False

    def prefetch_assets(self, rec):
        if not self.prefetcher:
            return
        for u, t in rec.doc_links:
            if not self.host_ok(u) or not N.is_english(N.locale_of_url(u)):
                continue
            if re.search(r'\.pdf(\?|$)', u, re.I):
                self.prefetcher.submit(u, 'pdf')
            elif re.search(r'\.zip(\?|$)', u, re.I) and A.zip_name_suggests_cad(u, t):
                self.prefetcher.submit(u, 'zip')
        groups = collections.defaultdict(list)
        for url, width, alt, c in rec.image_cands:
            if self.host_ok(url) and (A.IMAGE_EXT.search(url) or c in ('srcset', 'jsonld')) \
                    and not A.CHROME_IMAGE.search(_filename(url)):
                groups[N.image_key(url)].append((url, width))
        for key, cands in groups.items():
            self._img_seen[key] += 1
            if self._img_seen[key] > 20:
                continue
            for u in self.image_tries(cands)[:2]:
                self.prefetcher.submit(u, 'image')

    def host_ok(self, url):
        return self.allowed is None or N.host_allowed(url, self.allowed)

    # -------------------------------------------------- asset decisions
    def judge_asset(self, url, kind, text, found_on, site_wide, fam_count, shared_limit):
        c = (self.ctx.get(found_on) or {}).get(url) or {}
        section, in_chrome = c.get('section'), c.get('in_chrome')
        link_text = c.get('link_text') or text or None
        cand = {'url': url, 'link_text': link_text, 'section': section, 'type': kind, 'found_on': found_on}
        named = self.names_family(_filename(url), text, c.get('link_text'))
        other = self.names_other(_filename(url), text, c.get('link_text'))
        if other and (not named or (len(other[1]) > len(named[1]) and not (
                kind == 'image' and self.names_strongly(_filename(url), text, c.get('link_text'))))):
            return self.decide('asset', 'drop', f'names another family ({other[0]}: "{other[1]}")', url=url, candidate=cand)
        named = named and named[0]
        loc = N.locale_of_url(url)
        host = urlsplit(url).hostname or ''
        if not N.is_english(loc):
            return self.decide('asset', 'drop', f'language copy (URL locale {loc})', url=url, candidate=cand)
        if not self.host_ok(url):
            if named:
                return self.unsure('asset_host', f'Is {host} an official source for this family\'s {kind}?', cand,
                                   [{'quote': named, 'source': url}], [{'quote': f'host {host} is not in the site allowlist', 'source': 'config'}],
                                   'the file names the family but is served from a host outside the allowlist', 'drop')
            return self.decide('asset', 'drop', f'host not in allowlist ({host})', url=url, candidate=cand)
        if in_chrome:
            if named:
                return self.decide('asset', 'keep', f'in page chrome but {named}', url=url, candidate=cand)
            return self.decide('asset', 'drop', 'in page chrome (header/footer/nav) and does not name the family', url=url, candidate=cand)
        if site_wide:
            if named:
                return self.decide('asset', 'keep', f'site-wide file but {named}', url=url, candidate=cand)
            return self.decide('asset', 'drop', f'site-wide (on >{CHROME_SHARE:.0%} of pages) and does not name the family', url=url, candidate=cand)
        if section and RELATED_SECTION.search(section):
            if named:
                return self.decide('asset', 'keep', f'in "{section}" section but {named}', url=url, candidate=cand)
            return self.unsure('asset_to_family', f'Does this {kind} belong to {self._cur["name"]}?', cand,
                               [{'quote': f'linked from {found_on}', 'source': found_on}],
                               [{'quote': f'link sits in the "{section}" section', 'source': found_on},
                                {'quote': 'file name and link text do not name the family', 'source': url}],
                               'link is in a related-products section; it may describe another product', 'drop')
        if fam_count >= 2 and not named:
            if kind == 'document' and fam_count > shared_limit:
                return self.decide('asset', 'keep', f'shared by {fam_count} families but linked from this family\'s page content'
                                   + (f' (section "{section}")' if section else ''), url=url, candidate=cand)
            if fam_count > shared_limit:
                return self.decide('asset', 'drop', f'shared by {fam_count} families and names none of them', url=url, candidate=cand)
            return self.unsure('asset_to_family', f'Does this {kind} belong to {self._cur["name"]}?', cand,
                               [{'quote': f'linked from this family\'s page content' + (f' (section "{section}")' if section else ''), 'source': found_on}],
                               [{'quote': f'also linked from {fam_count - 1} other families', 'source': 'link graph'},
                                {'quote': 'file name and link text do not name the family', 'source': url}],
                               'a shared file in product content; the rules cannot tell which families it covers', 'keep')
        return self.decide('asset', 'keep', named or ('linked from family page content' + (f' (section "{section}")' if section else '')),
                           url=url, candidate=cand)

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
        links.sort(key=lambda x: 0 if A.classify_doc(x[0], x[1]) in A.PRIMARY else 1)
        n_pdf = 0
        for u, text, found_on in links:
            key = N.match_key(u, drop_asset_params=True)
            if key in seen:
                continue
            seen.add(key)
            cad = A.cad_from_url(u)
            is_zip = bool(re.search(r'\.zip(\?|$)', u, re.I))
            kind = 'cad' if cad else 'archive' if is_zip else 'document'
            dec = self.judge_asset(u, kind, text, found_on, key in chrome, self.doc_fam_counts.get(key, 0), DOC_SHARED_LIMIT)
            if dec == 'drop' or (dec == 'unsure' and not self.last_default_keep()):
                continue
            if cad:
                cads.append({'url': u, **cad, 'gated': False, 'found_on': found_on, 'variant_skus': []})
                continue
            if is_zip:
                if A.zip_name_suggests_cad(u, text):
                    z = self.zip_cad(u, text, found_on)
                    if z:
                        cads.append(z)
                    else:
                        self.decide('asset', 'drop', 'archive without CAD files (or download failed)', url=u)
                else:
                    self.decide('asset', 'drop', 'archive whose name does not suggest CAD', url=u)
                continue
            if n_pdf >= MAX_PDFS_PER_FAMILY:
                self.decide('asset', 'drop', f'per-family document cap ({MAX_PDFS_PER_FAMILY})', url=u)
                continue
            n_pdf += 1
            d = self.process_doc(u, text, found_on)
            if d:
                docs.append(d)
        return docs, cads

    def l1_dead(self, url):
        l = getattr(self, 'l1_assets', {}).get(url)
        return l.status if l and l.status >= 400 else None

    def process_doc(self, url, text, found_on):
        if self.l1_dead(url):
            self.decide('asset', 'drop', f'dead link (L1 status {self.l1_dead(url)}); not downloaded', url=url)
            return None
        r = self.fetcher.get(url, kind='pdf', purpose='pdf')
        c = (self.ctx.get(found_on) or {}).get(url) or {}
        if self.fetcher.response_blocked(r):
            doc_type = A.classify_doc(url, ' '.join(x for x in (text, c.get('link_text'), c.get('section')) if x))
            self.decide('asset', 'keep', f'download blocked ({r.status or r.error}); kept from link evidence, typed from URL/link text',
                        url=url, blocked=True)
            return {'url': url, 'doc_type': doc_type, 'priority': 'primary' if doc_type in A.PRIMARY else 'secondary',
                    'lang': A.detect_lang('', url)[0], 'title': text or None, 'revision_date': None, 'sha256': None,
                    'bytes': None, 'http_status': r.status, 'mime_verified': False, 'found_on': found_on, 'variant_skus': []}
        if not r.ok:
            self.decide('asset', 'drop', f'download failed ({r.status or r.error})', url=url)
            return None
        before = collections.Counter(self.flags)
        d = self.process_pdf(url, text, found_on)
        if d is None:
            why = [k for k in self.flags if self.flags[k] > before.get(k, 0)]
            self.decide('asset', 'drop', 'document excluded: ' + (', '.join(why) or 'not usable'), url=url)
            return None
        hint_text = ' '.join(x for x in (c.get('link_text'), c.get('section')) if x)
        hint = A._match_rules(hint_text.lower()) if hint_text and not A.GENERIC_LINK_TEXT.match(hint_text) else None
        content = A._match_rules(((d.get('_page_texts') or [''])[0] or '')[:1500].lower()) if d.get('_page_texts') else None
        if d['doc_type'] == 'other_doc' and hint:
            d['doc_type'] = hint
            self.decide('doc_type', 'keep', f'typed "{hint}" from link text/section "{hint_text}" (content undecided)', url=url)
        elif content and d['doc_type'] != content and {d['doc_type'], content} & A.PRIMARY:
            self.unsure('doc_type', f'Is this document a {d["doc_type"]} or a {content}?',
                        {'url': url, 'link_text': c.get('link_text') or text or None, 'section': c.get('section'), 'type': 'document', 'found_on': found_on},
                        [{'quote': (d.get('title') or text or _filename(url))[:200], 'source': url, 'type': d['doc_type']}],
                        [{'quote': ((d.get('_page_texts') or [''])[0] or '')[:200], 'source': url, 'page': 1, 'type': content}],
                        'URL/link/title say one type, the first page reads as another', f'keep as {d["doc_type"]}')
        d['priority'] = 'primary' if d['doc_type'] in A.PRIMARY else 'secondary'
        return d

    # -------------------------------------------------- images
    @staticmethod
    def image_tries(cands):
        ranked = sorted(dict.fromkeys(cands), key=lambda c: A.rank_candidate(*c), reverse=True)
        tries = [u for u, _ in ranked]
        if tries and A.SIZE_MARK.search(tries[0]):
            tries = A.original_candidates(tries[0]) + tries
        return list(dict.fromkeys(tries))

    def measure_image(self, tries):
        for u in tries[:4]:
            if self.l1_dead(u):
                continue
            resp = self.fetcher.get(u, kind='image', purpose='image')
            if self.fetcher.response_blocked(resp):
                self.decide('asset', 'drop', f'image download blocked ({resp.status or resp.error})', url=u, blocked=True)
                continue
            if not resp.ok or not resp.content_type.startswith('image'):
                continue
            w, h, ph = A.image_dims_phash(resp.body)
            if w and h:
                return u, w, h, ph
        return None

    def process_images(self, fam_pages, chrome, family_counts):
        groups = collections.OrderedDict()
        for r in fam_pages:
            for url, width, alt, ctx in r.image_cands:
                if not (A.IMAGE_EXT.search(url) or ctx in ('srcset', 'jsonld')):
                    continue
                key = N.image_key(url)
                key = self.img_alias.get(key, key)   # L1: srcset / wrapping link are versions of one image
                g = groups.setdefault(key, {'cands': [], 'alt': alt, 'found_on': r.url, 'first': url})
                g['cands'].append((url, width))
        images = []
        for key, g in groups.items():
            url, alt = g['first'], g['alt'] or ''
            name = _filename(url)
            if A.CHROME_IMAGE.search(name) or A.CHROME_IMAGE.search(alt):
                if not self.names_family(name, alt) or (self.names_other(name, alt) and not self.names_strongly(name, alt)):
                    self.decide('asset', 'drop', 'logo/icon/banner-like image name or alt text', url=url, alt=alt)
                    continue
            if (CHART_IMAGE.search(name) or CHART_IMAGE.search(alt)) and not DIMENSION_WORDS.search(name + ' ' + alt):
                self.decide('asset', 'drop', 'chart / graph image (performance data), not a product view (SPEC 4)', url=url)
                continue
            if A.NON_PRODUCT_PHOTO.search(name) or A.NON_PRODUCT_PHOTO.search(alt):
                self.decide('asset', 'drop', 'installation / lifestyle photo (SPEC 4)', url=url)
                continue
            dec = self.judge_asset(url, 'image', alt, g['found_on'], key in chrome, family_counts.get(key, 0), IMAGE_SHARED_LIMIT)
            if dec == 'drop' or (dec == 'unsure' and not self.last_default_keep()):
                continue
            if len(images) >= MAX_IMAGES_PER_FAMILY:
                self.decide('asset', 'drop', f'per-family image cap ({MAX_IMAGES_PER_FAMILY})', url=url)
                continue
            dims = [self.l1_dims[u] for u, _ in g['cands'] if u in self.l1_dims]
            declared = [w for _, w in g['cands'] if w]
            if dims and max(min(d) for d in dims) < 300 and (not declared or max(declared) < 300):
                self.decide('asset', 'drop', 'below 300 px per L1 width/height (not downloaded)', url=url)
                continue
            known = sorted(((self.l1_dims[u], u) for u, _ in g['cands'] if u in self.l1_dims), key=lambda x: -x[0][0] * x[0][1])
            if known and min(known[0][0]) >= 300 and known[0][0][0] >= max(declared or [0]):
                # L1 width/height of the largest version: no download needed (no phash for dedupe)
                (w, h), u = known[0]
                got = (u, w, h, None)
            else:
                got = self.measure_image(self.image_tries(g['cands']))
            if not got:
                self.decide('asset', 'drop', 'image could not be downloaded or measured', url=url)
                continue
            u, w, h, ph = got
            if min(w, h) < 300:
                self.decide('asset', 'drop', f'below 300 px ({w}x{h})', url=u)
                continue
            dup = next((im for im in images if N.phash_distance(im['phash'], ph) is not None
                        and N.phash_distance(im['phash'], ph) <= PHASH_SAME_IMAGE), None)
            if dup:
                if w * h > dup['width'] * dup['height']:
                    dup.update(url=u, width=w, height=h, phash=ph)
                self.decide('asset', 'drop', 'rendition of an image already kept (phash)', url=u)
                continue
            images.append({'url': u, 'image_type': A.image_type_of(u, g['alt']), 'width': w, 'height': h,
                           'phash': ph, 'found_on': g['found_on']})
        return images

    # -------------------------------------------------- specs
    def merge_spec(self, fname, cands):
        m = merge_field(fname, cands)
        if m and m.get('_pdf_disagreement') and self._cur:
            shown = json.dumps(m['value'], sort_keys=True, default=str)
            ev = lambda c: {'quote': (c.get('raw') or str(c['value']))[:200], 'source': c['source']['url'],
                            'page': c['source'].get('page'), 'value': c['value']}
            pdfs = [c for c in cands if c['kind'] in ('sheet', 'otherpdf')]
            self.unsure('spec_value', f'Which {fname} value is right for {self._cur["name"]}?',
                        {'url': m['sources'][0]['url'], 'link_text': None, 'section': fname, 'type': 'spec'},
                        [ev(c) for c in pdfs if json.dumps(c['value'], sort_keys=True, default=str) == shown][:3],
                        [ev(c) for c in pdfs if json.dumps(c['value'], sort_keys=True, default=str) != shown][:3],
                        'PDFs disagree; the spec-sheet value is shown by precedence', 'keep displayed value')
        return m

    def spec_conflicts(self, fam):
        for f, s in fam['specs'].items():
            if s.get('cross_check') != 'conflict':
                continue
            src = s['sources'][0]
            self.unsure('page_vs_pdf_conflict', f'Page and PDF disagree on {f} for {fam["name"]}: which is right?',
                        {'url': src['url'], 'link_text': None, 'section': f, 'type': 'spec'},
                        [{'quote': s.get('raw_text'), 'source': src['url'], 'page': src.get('page'), 'value': s['value']}],
                        [{'quote': a.get('raw_text'), 'source': a['sources'][0]['url'], 'page': a['sources'][0].get('page'),
                          'value': a['value']} for a in s.get('alt_values', [])][:3],
                        'page and PDF values contradict (SPEC 6a conflict); both are kept and flagged', 'keep both (conflict)')

    # -------------------------------------------------- assets never seen on a fetched page (L0 inventory)
    def assign_orphans(self, families, refs, recs):
        linked = set()
        for r in recs:
            linked |= {N.match_key(u, drop_asset_params=True) for u, _ in r.doc_links}
            linked |= {N.image_key(c[0]) for c in r.image_cands}
        n_kept = 0
        seen = set()
        for l in self.links.assets():
            key = N.image_key(l.url) if l.url_type == 'image' else N.match_key(l.url, drop_asset_params=True)
            if key in linked or key in seen or l.found_on:
                continue
            seen.add(key)
            name = _filename(l.url)
            if not N.is_english(N.locale_of_url(l.url)):
                self.decide('asset', 'drop', 'orphan: language copy', url=l.url, orphan=True)
                continue
            if not self.host_ok(l.url):
                self.decide('asset', 'drop', 'orphan: host not in allowlist', url=l.url, orphan=True)
                continue
            if l.url_type == 'image' and A.CHROME_IMAGE.search(name):
                self.decide('asset', 'drop', 'orphan: logo/icon-like image name', url=l.url, orphan=True)
                continue
            low, flat = name.lower(), _flat(name)
            hits = {}
            for i, ref in enumerate(refs):
                strong = [c for c in ref['_strong'] if self._code_in(c, low, flat)]
                if strong:
                    hits[i] = max(strong, key=len)
            cand = {'url': l.url, 'link_text': None, 'section': None, 'type': l.url_type, 'found_on': None}
            if not hits:
                self.decide('asset', 'drop', 'orphan: not linked from any fetched product page and names no family', url=l.url, orphan=True)
                continue
            best = max(len(c) for c in hits.values())
            top = [i for i, c in hits.items() if len(c) == best]
            if len(top) == 1 and best >= 4:
                i = top[0]
                self._cur = refs[i]
                ok = self.attach_orphan(families[i], l, hits[i])
                self._cur = None
                n_kept += bool(ok)
            else:
                self.unsure('asset_to_family', f'Which family does {name} belong to?', cand,
                            [{'quote': f'file name contains "{hits[i]}"', 'source': l.url, 'family_id': refs[i]['family_id']} for i in top[:5]],
                            [{'quote': 'not linked from any fetched product page', 'source': 'link graph'}],
                            'orphan file matches several families (or only a short code)', 'drop',
                            family={'candidates': [refs[i]['family_id'] for i in top[:10]]})
        return n_kept

    def attach_orphan(self, fam, l, code):
        why = f'orphan from the link inventory; file name contains identifier "{code}"'
        if l.url_type == 'image':
            got = self.measure_image([l.url])
            if not got or min(got[1], got[2]) < 300:
                self.decide('asset', 'drop', 'orphan image missing or below 300 px', url=l.url, orphan=True)
                return False
            u, w, h, ph = got
            if any(N.phash_distance(im['phash'], ph) is not None and N.phash_distance(im['phash'], ph) <= PHASH_SAME_IMAGE
                   for im in fam['images']) or len(fam['images']) >= MAX_IMAGES_PER_FAMILY:
                self.decide('asset', 'drop', 'orphan image duplicates a kept image (or cap)', url=l.url, orphan=True)
                return False
            fam['images'].append({'url': u, 'image_type': A.image_type_of(u, ''), 'width': w, 'height': h, 'phash': ph,
                                  'found_on': None})
        elif l.url_type in ('cad', 'bim') or A.cad_from_url(l.url):
            cad = A.cad_from_url(l.url)
            if not cad or any(N.match_key(c['url']) == N.match_key(l.url) for c in fam['cad']):
                self.decide('asset', 'drop', 'orphan CAD not recognised or already listed', url=l.url, orphan=True)
                return False
            fam['cad'].append({'url': l.url, **cad, 'gated': False, 'found_on': None, 'variant_skus': []})
        elif l.url_type == 'pdf' or A.DOC_EXT.search(l.url):
            if len(fam['documents']) >= MAX_PDFS_PER_FAMILY:
                return False
            d = self.process_doc(l.url, '', None)
            if not d:
                return False
            fam['documents'].append({k: v for k, v in d.items() if not k.startswith('_')})
        else:
            self.decide('asset', 'drop', f'orphan of type {l.url_type} not attached', url=l.url, orphan=True)
            return False
        self.decide('asset', 'keep', why, url=l.url, orphan=True)
        self.flag('asset_from_link_inventory_not_on_page', l.url)
        return True

    # -------------------------------------------------- run
    def run(self):
        t0, started = time.monotonic(), now_iso()
        ls = self.links
        self.l1_links = ls.links_on()
        self.l1_assets = {l.url: l for l in ls.links if l.url_type != 'page' and l.status is not None}
        self._img_seen = collections.Counter()
        for row, why in ls.skipped:
            self.decide('input', 'drop', why, row=row)
        # 1. ingest and tag
        cands = []
        for u in ls.pages:
            why = self.url_reject(u)
            if why:
                self.decide('page_role', 'drop', why, url=u)
            else:
                cands.append(u)
        self.log(f'[{self.site}] {ls.level}: {len(ls.pages)} pages, {len(ls.assets())} assets in the link file; '
                 f'{len(cands)} candidate pages')
        # 2. edges: page snapshots or one fetch per candidate page; assets prefetched on other hosts meanwhile
        self.prefetcher = AssetPrefetcher(self.fetcher) if self.prefetch and self.allowed is not None else None
        recs, by_key = [], {}
        for i, u in enumerate(cands, 1):
            res = self.guarded('page_crashed', u, self.load_page, u)
            if res is None:
                self.decide('page_role', 'drop', 'page processing crashed (see flags)', url=u)
                continue
            rec, err, blocked = res
            if err:
                self.decide('page_role', 'drop', err, url=u, **({'blocked': True} if blocked else {}))
                if blocked:
                    self.flag('page_request_blocked', u)
                continue
            keys = {N.match_key(rec.url), N.match_key(rec._canonical)}
            dup = next((by_key[k] for k in keys if k in by_key), None)
            if dup:
                self.decide('page_role', 'drop', f'duplicate of {dup.url} (same final or canonical URL)', url=u)
                continue
            for k in keys:
                by_key[k] = rec
            recs.append(rec)
            if rec._score >= PRODUCT_SCORE_THRESHOLD - 2:
                self.prefetch_assets(rec)
            if i % PROGRESS_EVERY == 0:
                self.log(f'  pages {i}/{len(cands)} ({self.fetcher.stats["requests"]} requests, {time.monotonic() - t0:.0f}s)')
        if self.prefetcher:
            self.log(f'[{self.site}] waiting for asset prefetch ...')
            self.prefetcher.close()
        if self.allowed is None:
            detected, _ = H.detect_asset_hosts(recs, self.page_hosts)
            self.allowed = list(self.page_hosts) + detected
        t_pages = time.monotonic() - t0
        # 3. page roles (page score + URL-template vote)
        templates = D.build_templates([r.url for r in recs])
        tmpl_of = {u: k for k, us in templates.items() for u in us}
        tscores = collections.defaultdict(list)
        for r in recs:
            tscores[tmpl_of.get(r.url)].append(r._score)
        tavg = {k: sum(v) / len(v) for k, v in tscores.items()}
        products, roles = [], collections.Counter()
        TH = PRODUCT_SCORE_THRESHOLD
        for r in recs:
            t = tmpl_of.get(r.url)
            avg, listing = tavg.get(t, 0.0), 'listing_like' in r._signals
            if r._score >= TH or (r._score >= TH - 2 and avg >= TH and not listing):
                products.append(r)
                roles['product'] += 1
                self.decide('page_role', 'keep', f'product page (score {r._score}, template {t} avg {avg:.1f})', url=r.url, signals=r._signals)
            elif listing and listing_with_product_evidence(r._signals, TH):
                products.append(r)
                roles['product (listing cue, unsure)'] += 1
                pos = [{'quote': f'{k} (+{v})', 'source': r.url} for k, v in r._signals.items() if v > 0]
                self.unsure('page_role', 'Is this a product page or a category listing?',
                            {'url': r.url, 'link_text': r.name, 'section': ' > '.join(r.crumbs) or None, 'type': 'page', 'found_on': None},
                            pos, [{'quote': 'links to more than 15 pages in its own section (listing_like -4)', 'source': r.url}],
                            'listing cue conflicts with product evidence', 'keep', family={})
            elif r._score >= TH - 2 and not listing:
                roles['unsure'] += 1
                pos = [{'quote': f'{k} (+{v})', 'source': r.url} for k, v in r._signals.items() if v > 0]
                self.unsure('page_role', 'Is this a product page?',
                            {'url': r.url, 'link_text': r.name, 'section': ' > '.join(r.crumbs) or None, 'type': 'page', 'found_on': None},
                            pos, [{'quote': f'score {r._score} < {TH}; URL template {t} averages {avg:.1f}', 'source': 'page roles'}],
                            'product signals are borderline', 'drop', family={})
            else:
                roles['listing' if listing else 'other'] += 1
                self.decide('page_role', 'drop', 'listing page' if listing else f'not a product page (score {r._score})',
                            url=r.url, signals=r._signals)
        # site-wide assets: on more than CHROME_SHARE of all pages read
        counts = collections.Counter()
        for r in recs:
            counts.update({N.match_key(u, drop_asset_params=True) for u, _ in r.doc_links} | {N.image_key(c[0]) for c in r.image_cands})
        chrome = {k for k, c in counts.items() if c / len(recs) > CHROME_SHARE and c >= 3} if len(recs) >= CHROME_MIN_PAGES else set()
        # 4. family grouping
        fixed, fixed_ev = SP.profile_assignments(self.profile, products)
        if self.profile:
            self.log(f'[{self.site}] site profile: {self.profile["family_shape"]}; {len(fixed)} of {len(products)} product pages placed by it')
        groups, evidence, g_unsure = G.group_pages(products, lambda r: self.ctx.get(r.url), self.resolved_links, fixed, fixed_ev)
        self.doc_fam_counts, family_counts = collections.Counter(), collections.Counter()
        for g in groups:
            self.doc_fam_counts.update({N.match_key(u, drop_asset_params=True) for r in g for u, _ in r.doc_links})
            family_counts.update({N.image_key(c[0]) for r in g for c in r.image_cands})
        refs = [self.make_ref(g) for g in groups]
        idx = collections.defaultdict(set)
        for r in refs:
            for c in r['_codes']:
                idx[c].add(r['family_id'])
        self.code_index = sorted(idx.items(), key=lambda x: -len(x[0]))
        merges = []
        for gi, ev in evidence.items():
            merges.append({'family_id': refs[gi]['family_id'], 'pages': [r.url for r in groups[gi]], 'evidence': ev})
            self.decide('family_grouping', 'keep', '; '.join(ev), url=groups[gi][0].url, family_id=refs[gi]['family_id'],
                        pages=[r.url for r in groups[gi]])
        for u in g_unsure:
            a, b = groups[u['group']][0], groups[u['other_group']][0]
            self.unsure('family_grouping', f'Is {a.url} part of the same family as {b.url}?',
                        {'url': a.url, 'link_text': a.name, 'section': u['leaf'], 'type': 'page', 'found_on': None},
                        [{'quote': f'same breadcrumb leaf "{u["leaf"]}" and identifier stem "{u["stem"]}"', 'source': a.url}],
                        [{'quote': f'base names differ: "{u["name"]}" vs "{u["other_name"]}"; no shared spec sheet or sizes block', 'source': b.url}],
                        'stem and breadcrumb match but nothing else links the pages', 'keep separate',
                        family={k: refs[u['other_group']][k] for k in ('family_id', 'name', 'series_code', 'canonical_url', 'identifiers')})
        # 5-8. families through the existing extraction code, with evidence-based asset decisions
        families, kept_refs, ids = [], [], collections.Counter()
        for i, g in enumerate(groups, 1):
            self._cur = refs[i - 1]
            fam = self.guarded('family_crashed', g[0].url, self.build_family, g, chrome, family_counts)
            if fam is None:
                continue
            fam['series_code'] = self._cur['series_code']
            if len(g) > 1:
                fam['name'] = self._cur['name']
                grouped_variants(fam, g, self.page_price)
            self.spec_conflicts(fam)
            ids[fam['family_id']] += 1
            if ids[fam['family_id']] > 1:
                fam['family_id'] += f'-{ids[fam["family_id"]]}'
            families.append(fam)
            kept_refs.append(dict(self._cur, _strong={c for c in self._cur['_codes']
                                                      if _flat(c) in {_flat(x) for x in self._cur['identifiers'] + [self._cur['series_code'] or '']}}))
            if i % PROGRESS_EVERY == 0:
                self.log(f'  families {i}/{len(groups)}')
        self._cur = None
        n_orphans = self.assign_orphans(families, kept_refs, recs)
        for fam in accessory_families(families, keep_grouped_pages=True,
                                      grouped={f['canonical_url'] for f in families if f.get('_grouped')}):
            self.flag('accessory_models_not_variants', fam['canonical_url'])
        for fam in families:
            fam.pop('_grouped', None)
        self.evidence.write_manifest()

        def pct(pred):
            return round(sum(1 for f in families if pred(f)) / len(families), 4) if families else 0.0
        dec_counts = collections.Counter((d['kind'], d['decision']) for d in self.decisions)
        unsure_counts = collections.Counter(d['unsure_kind'] for d in self.decisions if d['decision'] == 'unsure')
        blocked_hosts = dict(self.fetcher.blocked_hosts) if hasattr(self.fetcher, 'blocked_hosts') else {}
        wall = round(time.monotonic() - t0, 1)
        return {
            'schema_version': '1.0', 'site': self.site, 'input_url': self.cfg['input_url'], 'run_at': started,
            'agent': {'name': AGENT_NAME + '-process', 'version': AGENT_VERSION},
            'site_profile': {
                'fetch_mode': 'link-file', 'level': ls.level, 'links_file': Path(ls.path).name, 'blocked': bool(blocked_hosts),
                'input': {'pages': len(ls.pages), 'assets': len(ls.assets()), 'skipped_rows': len(ls.skipped),
                          'candidate_pages': len(cands), 'pages_read': len(recs), 'page_sources': dict(self.page_sources)},
                'page_roles': dict(roles),
                'hosts': {'page_hosts': self.page_hosts, 'allowed_hosts': self.allowed, 'blocked_hosts': blocked_hosts},
                'grouping': {'families': len(groups), 'multi_page_families': len(merges),
                             'pages_in_multi_page_families': sum(len(m['pages']) for m in merges), 'merges': merges},
            },
            'families': families,
            'coverage': {
                'families': len(families), 'sitemap_families': None,
                'pct_with_specs': pct(lambda f: bool(f['specs'])),
                'pct_with_spec_sheet': pct(lambda f: any(d['doc_type'] in SPEC_SHEET for d in f['documents'])),
                'pct_with_image': pct(lambda f: bool(f['images'])),
                'pct_with_cad': pct(lambda f: bool(f['cad'])),
                'pct_with_price': pct(lambda f: any(p['availability'] == 'price_shown' for v in f['variants'] for p in v['prices'])),
            },
            'unlinked': [],
            'flags': [f'{k}: {v}' + (f' (e.g. {self.flag_examples[k]})' if k in self.flag_examples else '')
                      for k, v in sorted(self.flags.items())],
            'run_stats': {**self.fetcher.stats, 'finished_at': now_iso(), 'limit': None, 'wall_seconds': wall,
                          'page_phase_seconds': round(t_pages, 1),
                          'requests_by_purpose': dict(getattr(self.fetcher, 'purpose_stats', {})),
                          'blocked_requests': len(getattr(self.fetcher, 'blocked', [])),
                          'orphan_assets_attached': n_orphans,
                          'decisions': {f'{k}:{d}': v for (k, d), v in sorted(dec_counts.items())},
                          'unsure_by_kind': dict(unsure_counts)},
        }


def write_process_outputs(run, decisions, out_dir):
    path = write_outputs(run, out_dir)
    with open(Path(out_dir) / f'{run["site"]}.decisions.jsonl', 'w') as f:
        for d in decisions:
            f.write(json.dumps({'site': run['site'], **d}, ensure_ascii=False, default=str) + '\n')
    return path
