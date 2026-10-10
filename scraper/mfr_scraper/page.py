"""HTML parsing primitives shared by discovery and extraction. All site-agnostic."""
import json
import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup, NavigableString, Tag

from . import specs as S

CHROME_PARENTS = ('header', 'footer', 'nav')


def soup_of(html):
    return BeautifulSoup(html, 'lxml')


CHROME_TOKENS = {'header', 'footer', 'navbar', 'nav', 'menu', 'megamenu', 'mega-menu', 'site-header', 'site-footer',
                 'main-nav', 'main-menu', 'cookie', 'cookie-banner', 'cookie-notice', 'breadcrumb', 'breadcrumbs',
                 'masthead', 'topbar', 'top-bar'}


def _in_chrome(el):
    for parent in el.parents:
        if not isinstance(parent, Tag) or parent.name in ('html', 'body', 'main', '[document]'):
            continue
        if parent.name in CHROME_PARENTS:
            return True
        tokens = [t.lower() for t in (parent.get('class') or [])] + [(parent.get('id') or '').lower()]
        if any(t in CHROME_TOKENS or t.endswith(('-header', '-footer', '-navbar', '-menu')) for t in tokens if t):
            return True
    return False


def visible_text(soup):
    """Text a reader sees, one block per line. Used for evidence snapshots and quotes."""
    s = BeautifulSoup(str(soup), 'lxml')
    for t in s(['script', 'style', 'noscript', 'template', 'svg']):
        t.decompose()
    text = s.get_text('\n')
    lines = [re.sub(r'[ \t\xa0]+', ' ', l).strip() for l in text.splitlines()]
    return '\n'.join(l for l in lines if l)


def text_of(el):
    return re.sub(r'\s+', ' ', el.get_text(' ', strip=True)).strip()


def html_lang(soup):
    h = soup.find('html')
    return (h.get('lang') or '').strip().lower().replace('_', '-') if h else ''


def hreflang_alternates(soup, base):
    out = {}
    for l in soup.find_all('link', attrs={'rel': 'alternate', 'hreflang': True}):
        if l.get('href'):
            out[l['hreflang'].lower()] = urljoin(base, l['href'])
    return out


def jsonld_objects(soup):
    objs = []
    for s in soup.find_all('script', attrs={'type': 'application/ld+json'}):
        try:
            data = json.loads(s.string or s.get_text() or '')
        except (json.JSONDecodeError, TypeError):
            continue
        stack = [data]
        while stack:
            d = stack.pop()
            if isinstance(d, list):
                stack.extend(d)
            elif isinstance(d, dict):
                objs.append(d)
                if '@graph' in d:
                    stack.append(d['@graph'])
    return objs


def ld_type_is(obj, name):
    t = obj.get('@type')
    return name in (t if isinstance(t, list) else [t])


def links(soup, base):
    out = []
    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        if href.startswith(('mailto:', 'tel:', 'javascript:', '#')):
            continue
        out.append((urljoin(base, href), text_of(a)))
    return out


def breadcrumbs(soup):
    for o in jsonld_objects(soup):
        if ld_type_is(o, 'BreadcrumbList'):
            items = o.get('itemListElement') or []
            names = []
            for it in sorted(items, key=lambda i: i.get('position', 0) if isinstance(i, dict) else 0):
                if isinstance(it, dict):
                    n = it.get('name') or (it.get('item') or {}).get('name') if isinstance(it.get('item'), dict) else it.get('name')
                    if n:
                        names.append(str(n).strip())
            if names:
                return names
    el = soup.find(attrs={'class': re.compile(r'breadcrumb', re.I)}) or soup.find(attrs={'aria-label': re.compile('breadcrumb', re.I)})
    if el:
        parts = [text_of(x) for x in el.find_all(['a', 'span', 'li']) if text_of(x)]
        parts = [p for p in dict.fromkeys(parts) if len(p) < 80 and p not in ('/', '>', '»')]
        return parts
    return []


def product_name(soup):
    for o in jsonld_objects(soup):
        if ld_type_is(o, 'Product') and o.get('name'):
            return str(o['name']).strip()
    h1 = soup.find('h1')
    if h1 and text_of(h1):
        return text_of(h1)
    og = soup.find('meta', attrs={'property': 'og:title'})
    if og and og.get('content'):
        return og['content'].strip()
    return text_of(soup.title).split('|')[0].strip() if soup.title else ''


@dataclass
class Pair:
    label: str
    value: str
    field: str | None


def _value_after(label_el):
    """The value element paired with a label element (next sibling cell/element)."""
    if label_el.name == 'dt':
        dd = label_el.find_next_sibling('dd')
        return dd
    if label_el.name in ('th', 'td'):
        nxt = label_el.find_next_sibling(['td', 'th'])
        return nxt
    nxt = label_el.find_next_sibling()
    if nxt is not None:
        return nxt
    # label/value as text nodes inside one parent: "<li><b>Size:</b> 1/2 - 2</li>"
    tail = ''.join(str(s) for s in label_el.next_siblings if isinstance(s, NavigableString)).strip(' :\n\t')
    if tail:
        fake = BeautifulSoup(f'<span>{tail}</span>', 'lxml').span
        return fake
    return None


def label_value_pairs(soup):
    """Find label->value pairs in tables, definition lists, and div/label pairs anywhere on the page."""
    pairs, seen = [], set()
    candidates = soup.find_all(['th', 'td', 'dt', 'label', 'div', 'span', 'strong', 'b', 'p', 'h4', 'h5', 'h6', 'li'])
    for el in candidates:
        if _in_chrome(el):
            continue
        # Label elements are short and have no nested block content.
        if el.find(['table', 'ul', 'ol', 'div', 'dl']) is not None and el.name not in ('th', 'td', 'dt'):
            continue
        label = text_of(el)
        if not label or len(label) > 60:
            continue
        f = S.field_for_label(label)
        if not f:
            continue
        val_el = _value_after(el)
        if val_el is None:
            continue
        value = val_el.get_text('\n', strip=True)
        value = re.sub(r'[ \t\xa0]+', ' ', value).strip()
        if not value or len(value) > 400 or S.field_for_label(value) is not None:
            continue
        key = (f, value)
        if key in seen:
            continue
        seen.add(key)
        pairs.append(Pair(label, value, f))
    return pairs


def image_candidates(soup, base):
    """(url, declared_width, alt, context) for every image reference outside site chrome."""
    out = []
    for img in soup.find_all(['img', 'source']):
        if _in_chrome(img):
            continue
        alt = img.get('alt') or ''
        for attr in ('src', 'data-src', 'data-lazy-src', 'data-original', 'data-zoom-image', 'data-large_image'):
            if img.get(attr) and not img[attr].startswith('data:'):
                w = img.get('width')
                out.append((urljoin(base, img[attr]), int(w) if str(w or '').isdigit() else None, alt, 'img'))
        for attr in ('srcset', 'data-srcset'):
            if img.get(attr):
                for part in img[attr].split(','):
                    bits = part.strip().split()
                    if not bits:
                        continue
                    w = None
                    if len(bits) > 1 and bits[1].endswith('w') and bits[1][:-1].isdigit():
                        w = int(bits[1][:-1])
                    out.append((urljoin(base, bits[0]), w, alt, 'srcset'))
        a = img.find_parent('a', href=True)
        if a and re.search(r'\.(jpe?g|png|webp)(\?|$)', a['href'], re.I):
            out.append((urljoin(base, a['href']), None, alt, 'link'))
    for o in jsonld_objects(soup):
        if ld_type_is(o, 'Product'):
            imgs = o.get('image')
            for i in (imgs if isinstance(imgs, list) else [imgs]):
                if isinstance(i, dict):
                    i = i.get('url')
                if isinstance(i, str):
                    out.append((urljoin(base, i), None, 'jsonld', 'jsonld'))
    return out


def iframes(soup, base):
    return [urljoin(base, f['src']) for f in soup.find_all('iframe', src=True)]


PRICE_PATTERNS = [
    ('login_required', r'sign\s?in (?:for|to (?:see|view)) pric|log\s?in (?:for|to (?:see|view)) pric|login for pric|members? pric'),
    ('request_quote', r'request (?:a )?quote|call for pric|contact (?:us|your [\w ]{0,30}) for pric|price on request|get a quote'),
]


def price_signals(soup, text):
    """Price from schema.org offers, else an availability status from page wording."""
    for o in jsonld_objects(soup):
        if not ld_type_is(o, 'Product'):
            continue
        offers = o.get('offers')
        for off in (offers if isinstance(offers, list) else [offers]):
            if isinstance(off, dict) and off.get('price') not in (None, ''):
                try:
                    amount = float(str(off['price']).replace(',', ''))
                except ValueError:
                    continue
                return {'availability': 'price_shown', 'amount': amount,
                        'currency': (off.get('priceCurrency') or '').upper() or None,
                        'sku': off.get('sku') or o.get('sku'), 'quote': str(off['price'])}
    for status, pat in PRICE_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            line = next((l for l in text.splitlines() if re.search(pat, l, re.I)), m.group(0))
            return {'availability': status, 'quote': line.strip()[:200]}
    return {'availability': 'not_published', 'quote': None}


def product_skus(soup):
    skus = []
    for o in jsonld_objects(soup):
        if ld_type_is(o, 'Product'):
            if o.get('sku'):
                skus.append(str(o['sku']))
            offers = o.get('offers')
            for off in (offers if isinstance(offers, list) else [offers]):
                if isinstance(off, dict) and off.get('sku'):
                    skus.append(str(off['sku']))
    return list(dict.fromkeys(skus))


def path_tail(url):
    segs = [s for s in urlsplit(url).path.split('/') if s]
    return segs[-1] if segs else ''
