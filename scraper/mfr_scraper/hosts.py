"""Work out which hosts belong to a manufacturer, from nothing but its homepage URL.

- Page hosts: the homepage's registrable domain and all its subdomains (www.example.com -> example.com, *.example.com).
- Asset hosts: other hosts that serve documents or images referenced from many of the site's own
  product pages (CDNs, blob storage, document servers such as cdn.example.com or
  a PIM vendor's host). Third-party services (social, analytics, fonts, script CDNs, video) are excluded.

No per-site configuration is needed; a configured list (harness/config/sites.json) is only an override
and, for the evaluation sites, the reference the detection is checked against.
"""
import collections
import re
from urllib.parse import urlsplit

ASSET_SHARE = 0.25          # host must serve assets on at least this share of product pages ...
ASSET_MIN_PAGES = 2         # ... and on at least this many pages

DENY = re.compile(
    r'(^|\.)(facebook|fbcdn|twitter|twimg|x|linkedin|licdn|instagram|cdninstagram|pinterest|pinimg|youtube|ytimg|'
    r'youtu|vimeo|vimeocdn|google|googleapis|gstatic|googletagmanager|google-analytics|doubleclick|googlesyndication|'
    r'gravatar|hubspot|hs-sites|hsforms|hscollectedforms|hubspotusercontent-na1|addthis|sharethis|recaptcha|'
    r'cloudflareinsights|cdnjs|jsdelivr|unpkg|bootstrapcdn|fontawesome|typekit|fonts|adobe|demdex|omtrdc|'
    r'hotjar|clarity|bing|yahoo|tiktok|trustpilot|zendesk|intercom|cookielaw|onetrust|cookiebot|usercentrics|'
    r'wistia|brightcove|issuu|schema|w3|amazon-adsystem|criteo|taboola|outbrain)\.[a-z.]+$', re.I)

TWO_PART_SUFFIXES = {'co.uk', 'com.au', 'co.nz', 'com.br', 'co.jp', 'com.mx', 'co.za', 'com.cn', 'org.uk', 'ac.uk'}


def registrable_domain(host):
    host = (host or '').lower().strip('.')
    parts = host.split('.')
    if len(parts) >= 3 and '.'.join(parts[-2:]) in TWO_PART_SUFFIXES:
        return '.'.join(parts[-3:])
    return '.'.join(parts[-2:]) if len(parts) >= 2 else host


def page_hosts(input_url):
    return [registrable_domain(urlsplit(input_url).hostname)]


def detect_asset_hosts(page_records, own_domains):
    """page_records: objects with .doc_links [(url, text)] and .image_cands [(url, w, alt, ctx)].
    Returns (hosts, evidence) where evidence maps host -> pages it appeared on."""
    per_host = collections.Counter()
    for r in page_records:
        hosts = {urlsplit(u).hostname for u, _ in r.doc_links} | {urlsplit(c[0]).hostname for c in r.image_cands}
        per_host.update(h.lower() for h in hosts if h)
    n = max(len(page_records), 1)
    chosen, evidence = [], {}
    for h, c in per_host.most_common():
        if any(h == d or h.endswith('.' + d) for d in own_domains) or DENY.search(h):
            continue
        evidence[h] = c
        if c >= ASSET_MIN_PAGES and c / n >= ASSET_SHARE:
            chosen.append(h)
    return chosen, evidence
