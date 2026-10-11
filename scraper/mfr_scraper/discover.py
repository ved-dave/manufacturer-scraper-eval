"""Find candidate product URLs without hand-written per-site rules.

1. Sitemaps: robots.txt `Sitemap:` lines + common locations, followed recursively (indexes, .gz).
2. URL templates: page URLs are grouped by path shape; a path position whose values vary a lot
   becomes a wildcard (e.g. /product/*/* or /valves-actuators-controls/*/*/*).
3. Template classification: a few pages per template are fetched and scored for product-page
   signals (schema.org Product, spec label/value pairs, spec-like downloads, breadcrumbs ...).
   Templates whose average score passes the threshold are product templates.
"""
import collections
import gzip
import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from . import page as P
from .settings import MIN_TEMPLATE_URLS, N, PRODUCT_SCORE_THRESHOLD, TEMPLATE_SAMPLE_PAGES

FILE_EXT = re.compile(r'\.(pdf|zip|jpe?g|png|gif|webp|svg|dwg|dxf|stp|step|igs|iges|rfa|rvt|xlsx?|docx?|mp4|xml|txt|css|js)$', re.I)
NON_PRODUCT_WORDS = re.compile(
    r'(^|[/-])(news|blog|blogs|press|events?|careers?|jobs|about|about-us|contact|contact-us|privacy|terms|legal|'
    r'cookies?|login|account|cart|checkout|search|tag|tags|author|feed|investors?|locations?|sustainability|'
    r'webinars?|videos?|case-stud(?:y|ies)|insights?|articles?|faq|support|training|history|leadership)([/-]|$)', re.I)


def sitemap_urls(fetcher, base_url, log=print):
    root = f'{urlsplit(base_url).scheme}://{urlsplit(base_url).netloc}'
    robots = fetcher.robots(base_url)
    queue = list(dict.fromkeys(robots.sitemaps + [root + '/sitemap.xml', root + '/sitemap_index.xml']))
    seen, pages, lastmod = set(), [], {}
    while queue and len(seen) < 500:
        sm = queue.pop(0)
        if sm in seen:
            continue
        seen.add(sm)
        r = fetcher.get(sm, kind='other')
        if not r.ok:
            continue
        body = r.body
        if sm.endswith('.gz') or body[:2] == b'\x1f\x8b':
            try:
                body = gzip.decompress(body)
            except OSError:
                continue
        text = body.decode('utf-8', errors='replace')
        if '<sitemapindex' in text:
            queue += [u for u in re.findall(r'<loc>\s*([^<\s]+)\s*</loc>', text)]
            continue
        for block in re.findall(r'<url>(.*?)</url>', text, re.S):
            m = re.search(r'<loc>\s*([^<\s]+)\s*</loc>', block)
            if not m:
                continue
            u = m.group(1).replace('&amp;', '&')
            pages.append(u)
            lm = re.search(r'<lastmod>\s*([^<\s]+)\s*</lastmod>', block)
            if lm:
                lastmod[u] = lm.group(1)
    log(f'  sitemaps read: {len(seen)}; urls: {len(pages)}')
    return list(dict.fromkeys(pages)), lastmod, sorted(seen)


LISTING_PARAMS = re.compile(r'(^|&)(page|p|pg|paged|sort|sortby|order|orderby|filter|view|limit|per_page|q|s|query|'
                            r'search|productid|start|offset|lang|_lang|language|utm_[a-z]+)=', re.I)


def candidate_pages(urls, allowed_hosts):
    """HTML page URLs on allowed hosts, English locale, not obviously non-product."""
    out = []
    for u in urls:
        path = urlsplit(u).path
        if LISTING_PARAMS.search(urlsplit(u).query):
            continue
        if FILE_EXT.search(path) or not N.host_allowed(u, allowed_hosts):
            continue
        if not N.is_english(N.locale_of_url(u)):
            continue
        if NON_PRODUCT_WORDS.search(path):
            continue
        out.append(u)
    return out


def _segments(u):
    return [s for s in urlsplit(u).path.split('/') if s]


def build_templates(urls):
    """Group URLs by path shape. Returns {template: [urls]}."""
    by_shape = collections.defaultdict(list)
    for u in urls:
        segs = _segments(u)
        if not segs:
            continue
        by_shape[(len(segs), segs[0].lower())].append(u)
    templates = {}
    for (depth, first), group in by_shape.items():
        variety = []
        for i in range(depth):
            values = collections.Counter(_segments(u)[i].lower() for u in group)
            variety.append(values)
        parts = []
        for i, values in enumerate(variety):
            # A position is fixed when one value dominates the group; otherwise it is a wildcard.
            top, count = values.most_common(1)[0]
            parts.append(top if count >= 0.8 * len(group) or i == 0 and len(values) == 1 else '*')
        if len(group) == 1:
            parts = [_segments(group[0])[i].lower() if i < depth - 1 else '*' for i in range(depth)]
        key = '/' + '/'.join(parts)
        templates.setdefault(key, []).extend(group)
    return templates


def score_product_page(soup, url, html_text):
    """Heuristic product-page score; returns (score, signals)."""
    signals = {}
    ld = P.jsonld_objects(soup)
    if any(P.ld_type_is(o, 'Product') for o in ld):
        signals['jsonld_product'] = 3
    og = soup.find('meta', attrs={'property': 'og:type'})
    if og and 'product' in (og.get('content') or '').lower():
        signals['og_product'] = 2
    pairs = P.label_value_pairs(soup)
    recognised = [p for p in pairs if p.field]
    if len(recognised) >= 2:
        signals['spec_pairs'] = 3
    elif recognised:
        signals['spec_pair'] = 1
    docs = [a for a in P.links(soup, url) if re.search(r'\.(pdf|zip|dwg|stp|step|rfa)(\?|$)', a[0], re.I)]
    if any(re.search(r'spec|data.?sheet|submittal|technical|\bds\b|[-_]ds[-_.]|dimension', (h + ' ' + t), re.I) for h, t in docs):
        signals['spec_download'] = 2
    elif docs:
        signals['download'] = 1
    if P.breadcrumbs(soup):
        signals['breadcrumb'] = 1
    if re.search(r'/(products?|p|item|model|series)/', urlsplit(url).path, re.I):
        signals['url_word'] = 1
    if re.search(r'\b(add to cart|sign in for pricing|request a quote|where to buy|model number|part number|sku)\b', html_text, re.I):
        signals['commerce_words'] = 1
    # Listing pages link to many distinct pages in the same section at the same or deeper level.
    here = _segments(url)
    section = {h.split('#')[0] for h, _ in P.links(soup, url)
               if _segments(h)[:1] == here[:1] and len(_segments(h)) >= len(here) and h.split('#')[0] != url}
    if len(section) > 15:
        signals['listing_like'] = -4
    return sum(signals.values()), signals


def classify_templates(fetcher, templates, log=print, sample=TEMPLATE_SAMPLE_PAGES):
    """Fetch a few pages per template and keep templates that look like product pages."""
    result = {}
    for key, urls in sorted(templates.items(), key=lambda kv: -len(kv[1])):
        if len(urls) < MIN_TEMPLATE_URLS and len(templates) > 3:
            continue
        step = max(1, len(urls) // sample)
        picks = sorted(urls)[::step][:sample]
        scores, details = [], []
        for u in picks:
            r = fetcher.get(u)
            if not r.ok or 'html' not in (r.content_type or 'text/html'):
                continue
            html = r.text()
            soup = BeautifulSoup(html, 'lxml')
            s, sig = score_product_page(soup, u, html)
            scores.append(s)
            details.append({'url': u, 'score': s, 'signals': sig})
        avg = sum(scores) / len(scores) if scores else 0.0
        # A template with no wildcard is a single page, not a family of product pages.
        is_product = avg >= PRODUCT_SCORE_THRESHOLD and '*' in key
        result[key] = {'urls': len(urls), 'avg_score': round(avg, 2), 'product': is_product, 'samples': details}
        log(f'  template {key:60} urls={len(urls):5} score={avg:4.1f} {"PRODUCT" if is_product else ""}')
    return result


def match_template(url, template_key):
    segs, parts = _segments(url), template_key.strip('/').split('/')
    return len(segs) == len(parts) and all(p == '*' or p == s.lower() for p, s in zip(parts, segs))


def crawl_navigation(fetcher, base_url, page_hosts, max_pages=150, max_depth=3, log=print):
    """Breadth-first crawl from the homepage through menus and category pages.

    Sitemaps are often incomplete (on Bray, 24 of 103 product families are missing from them), so
    this always runs alongside sitemap discovery. It follows page links on the site's own hosts,
    including pagination, up to max_depth hops and max_pages fetches, and returns every candidate
    page URL it saw.
    """
    seen, found = set(), []
    queue = [(base_url, 0)]
    while queue and len(seen) < max_pages:
        u, depth = queue.pop(0)
        key = u.split('#')[0]
        if key in seen:
            continue
        seen.add(key)
        r = fetcher.get(key)
        if not r.ok or 'html' not in (r.content_type or 'text/html'):
            continue
        soup = BeautifulSoup(r.text(), 'lxml')
        for h, _ in P.links(soup, r.final_url):
            h = h.split('#')[0]
            if not N.host_allowed(h, page_hosts) or FILE_EXT.search(urlsplit(h).path):
                continue
            q = urlsplit(h).query
            is_pagination = bool(re.search(r'(^|&)(page|p|pg|paged)=\d+', q, re.I))
            if candidate_pages([h], page_hosts):
                found.append(h)
            elif not is_pagination:
                continue
            if depth + 1 <= max_depth and h not in seen:
                queue.append((h, depth + 1))
    log(f'  navigation crawl: {len(seen)} pages fetched, {len(set(found))} candidate links')
    return list(dict.fromkeys(found))


def absolute(base, href):
    return urljoin(base, href)
