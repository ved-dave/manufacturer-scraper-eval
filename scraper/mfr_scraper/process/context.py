"""Link context derived from page HTML: what L1 records carry as link_text / section / in_chrome / link_kind.

L0 has no such fields, so the processing layer derives them from the page it fetched; L1 values win when present.
"""
import re
from urllib.parse import urljoin

from bs4 import Tag

from .. import page as P

HEADINGS = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
TAB_LABEL = re.compile(r'\b(tab|accordion|panel)[-_]?(title|label|heading|header|button)?\b', re.I)


def link_context(soup, base):
    """{absolute_url: {'link_text','section','in_chrome','link_kind'}} for a/img/source/iframe in document order."""
    out = {}
    section = None
    for el in soup.find_all(True):
        if not isinstance(el, Tag):
            continue
        name = el.name
        if name in HEADINGS or (name in ('button', 'a', 'li', 'span', 'div') and el.get('role') == 'tab'):
            t = P.text_of(el)
            if t and len(t) < 80:
                section = t
            continue
        if name == 'a' and el.get('href'):
            href = el['href'].strip()
            if href.startswith(('mailto:', 'tel:', 'javascript:', '#')):
                continue
            kind, url, text = 'a', urljoin(base, href), P.text_of(el)
        elif name in ('img', 'source'):
            src = el.get('src') or el.get('data-src') or el.get('srcset', '').split(' ')[0]
            if not src or src.startswith('data:'):
                continue
            kind, url, text = name, urljoin(base, src), el.get('alt') or ''
        elif name == 'iframe' and el.get('src'):
            kind, url, text = 'iframe', urljoin(base, el['src']), el.get('title') or ''
        else:
            continue
        if url not in out:
            out[url] = {'link_text': text or None, 'section': section, 'in_chrome': P._in_chrome(el), 'link_kind': kind}
    return out


def canonical_of(soup, base):
    el = soup.find('link', rel=lambda v: v and 'canonical' in (v if isinstance(v, list) else [v]), href=True)
    return urljoin(base, el['href'].strip()) if el else None
