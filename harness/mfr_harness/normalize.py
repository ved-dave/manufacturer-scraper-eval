"""URL, locale, and spec-value normalization shared by validate/score/legacy."""
import re
from fractions import Fraction
from urllib.parse import urlsplit, parse_qsl, urlencode, unquote, quote

# Query params that never change what a URL identifies.
TRACKING_PARAMS = re.compile(r'^(utm_.*|gclid|fbclid|msclkid|mc_cid|mc_eid|_ga|_gl|ref|source)$', re.I)
# Additional params that only select a cache-bust / rendition of the same asset.
ASSET_PARAMS = re.compile(r'^(itok|h|c|v|ver|sfvrsn|w|width|h|height|size|resize|fit|q|quality|format|fm|auto|dpr|crop)$', re.I)

LOCALE_SEG = re.compile(r'^[a-z]{2}(?:[-_][a-z]{2,3})?$', re.I)
LOCALE_QUERY_KEYS = ('lang', '_lang', 'language', 'locale', 'hl')

NA_LOCALES = {'en', 'en-us', 'en-ca'}

IMAGE_EXT = r'(?:jpe?g|png|gif|webp|avif|tiff?|bmp)'


def _split(url):
    s = urlsplit(url.strip())
    host = (s.hostname or '').lower()
    if host.startswith('www.'):
        host = host[4:]
    path = quote(unquote(s.path), safe="/-._~!$&'()*+,;=:@")
    return s, host, path


def match_key(url, drop_asset_params=False):
    """Key used to decide whether two URLs identify the same resource.
    Case-insensitive, scheme- and www-agnostic, trailing slash and tracking params removed."""
    s, host, path = _split(url)
    path = path.rstrip('/') or '/'
    q = [(k, v) for k, v in parse_qsl(s.query, keep_blank_values=True)
         if not TRACKING_PARAMS.match(k) and not (drop_asset_params and ASSET_PARAMS.match(k))]
    q.sort()
    key = host + path
    if q:
        key += '?' + urlencode(q)
    return key.lower()


def image_key(url):
    """Collapse known CMS/CDN rendition patterns so every size of one image shares a key."""
    s, host, path = _split(url)
    p = unquote(path).lower()
    p = re.sub(r'/styles/[^/]+/public/', '/', p)                    # Drupal image styles
    p = re.sub(r'/stencil/[^/]+/', '/stencil/', p)                  # BigCommerce
    p = re.sub(r'(\.' + IMAGE_EXT + r')\.(?:webp|avif)$', r'\1', p)  # Drupal x.jpg.webp
    p = re.sub(r'-\d{2,5}x\d{2,5}(?=\.' + IMAGE_EXT + r'$)', '', p)  # WordPress -300x212
    p = re.sub(r'-scaled(?=\.' + IMAGE_EXT + r'$)', '', p)            # WordPress -scaled
    p = re.sub(r'_\d{2,5}x\d{0,5}(?=\.' + IMAGE_EXT + r'$)', '', p)  # Shopify _600x
    p = re.sub(r'__\d+\.\d+(?=\.' + IMAGE_EXT + r'$)', '', p)        # BigCommerce __12345.1672251970
    p = re.sub(r'\.(?:jpe?g|png|webp|avif)$', '.img', p)             # same image, different encoding
    return host + p


def locale_of_url(url):
    """Best-effort locale from the URL: first path segment, '<xx>.' subdomain, or a lang query param."""
    s = urlsplit(url)
    for k, v in parse_qsl(s.query):
        if k.lower() in LOCALE_QUERY_KEYS and v:
            return v.lower().replace('_', '-')
    segs = [x for x in s.path.split('/') if x]
    if segs and LOCALE_SEG.match(segs[0]) and not re.match(r'^(id|no|pdf|img|css|js|api|app|cdn|doc|dl)$', segs[0], re.I):
        return segs[0].lower().replace('_', '-')
    host = (s.hostname or '').lower()
    sub = host.split('.')[0] if host.count('.') >= 2 else ''
    if len(sub) == 2 and sub not in ('ww',):
        return sub
    return None


def is_english(locale):
    return locale is None or locale.split('+')[0].startswith('en')


def market_flag(locale):
    if locale is None or locale in NA_LOCALES:
        return 'na'
    return 'non_na' if locale.startswith('en') else None


def host_allowed(url, allowed_hosts):
    host = (urlsplit(url).hostname or '').lower()
    for h in allowed_hosts:
        h = h.lower()
        if h.startswith('www.'):
            h = h[4:]
        if host == h or host.endswith('.' + h) or host == 'www.' + h:
            return True
    return False


def phash_distance(a, b):
    try:
        return bin(int(a, 16) ^ int(b, 16)).count('1')
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- spec values

SPEC_KINDS = {
    'size_range': 'size_range',
    'sizes_available': 'size_set',
    'size_unit': 'enum',
    'material_body': 'text',
    'material_trim': 'text',
    'material_seat': 'text',
    'material_seals': 'text',
    'end_connections': 'set',
    'pressure_rating': 'pressure',
    'temperature_range': 'temperature',
    'certifications': 'cert_set',
    'standards': 'set',
    'applications': 'set',
}

CERT_PATTERNS = [
    (r'nsf\W*(?:ansi\W*)?(?:can\W*)?61', 'NSF/ANSI 61'),
    (r'nsf\W*(?:ansi\W*)?372', 'NSF/ANSI 372'),
    (r'nsf\W*(?:ansi\W*)?14\b', 'NSF/ANSI 14'),
    (r'\bul\b|underwriters', 'UL'),
    (r'\bulc\b|ul\W*canada|c\W*ul\W*us', 'cULus'),
    (r'\bfm\b|factory\W*mutual', 'FM'),
    (r'\bcsa\b', 'CSA'),
    (r'\biapmo\b|\bupc\b', 'IAPMO/UPC'),
    (r'lead\W*free|low\W*lead', 'NSF/ANSI 372'),
]


def norm_token(s):
    return re.sub(r'[^a-z0-9./+]+', '', str(s).lower())


def cert_tokens(values):
    out = set()
    for v in values:
        s = str(v).lower()
        hit = False
        for pat, canon in CERT_PATTERNS:
            if re.search(pat, s):
                out.add(canon)
                hit = True
        if not hit:
            out.add(norm_token(v))
    return out


def parse_size(s):
    """'1-1/2' / '1 1/2' / '3/4' / '2' / 'DN50' / '1.5' -> float (inches or DN number)."""
    if s is None:
        return None
    t = str(s).lower().replace('"', '').replace('in', '').replace('nps', '').replace('dn', '').strip()
    m = re.fullmatch(r'(\d+)\s*[- ]\s*(\d+)/(\d+)', t)
    if m:
        return int(m.group(1)) + int(m.group(2)) / int(m.group(3))
    try:
        return float(Fraction(t))
    except (ValueError, ZeroDivisionError):
        return None


def to_psi(value, unit):
    u = (unit or 'psi').lower()
    v = float(value)
    return v * 14.5038 if u == 'bar' else v * 0.145038 if u == 'kpa' else v


def to_f(value, unit):
    u = (unit or 'F').upper()
    v = float(value)
    return v * 9 / 5 + 32 if u.startswith('C') else v


def set_f1(gold, pred):
    if not gold and not pred:
        return 1.0
    if not gold or not pred:
        return 0.0
    tp = len(gold & pred)
    if tp == 0:
        return 0.0
    p, r = tp / len(pred), tp / len(gold)
    return 2 * p * r / (p + r)


def _as_list(v):
    return v if isinstance(v, list) else [v]


def compare_spec(key, gold, pred):
    """Return a score in [0,1] comparing two spec_value dicts for field `key`."""
    kind = SPEC_KINDS.get(key, 'text')
    gv, pv = gold.get('value'), pred.get('value')
    try:
        if kind == 'set':
            return set_f1({norm_token(x) for x in _as_list(gv)}, {norm_token(x) for x in _as_list(pv)})
        if kind == 'cert_set':
            return set_f1(cert_tokens(_as_list(gv)), cert_tokens(_as_list(pv)))
        if kind == 'size_set':
            g = {round(parse_size(x), 4) for x in _as_list(gv) if parse_size(x) is not None}
            p = {round(parse_size(x), 4) for x in _as_list(pv) if parse_size(x) is not None}
            return set_f1(g, p)
        if kind == 'size_range':
            ok = [abs(parse_size(gv[k]) - parse_size(pv[k])) < 1e-6 for k in ('min', 'max')]
            return sum(ok) / 2
        if kind == 'pressure':
            g, p = to_psi(gv, gold.get('unit')), to_psi(pv, pred.get('unit'))
            return 1.0 if abs(g - p) <= 0.02 * max(abs(g), 1) else 0.0
        if kind == 'temperature':
            ok = [abs(to_f(gv[k], gold.get('unit')) - to_f(pv[k], pred.get('unit'))) <= 1.5 for k in ('min', 'max')]
            return sum(ok) / 2
        if kind == 'enum':
            return 1.0 if norm_token(gv) == norm_token(pv) else 0.0
        # free text (materials): word-token F1
        g = set(re.findall(r'[a-z0-9]+', str(gv).lower()))
        p = set(re.findall(r'[a-z0-9]+', str(pv).lower()))
        return set_f1(g, p)
    except (TypeError, ValueError, KeyError, AttributeError):
        return 0.0


# ---------------------------------------------------------------- refinement (SPEC 6a)

# General term -> words that make a value a more specific member of it.
MATERIAL_FAMILIES = {
    'plastic': ['pvc', 'cpvc', 'abs', 'ppsu', 'psu', 'pex', 'pp', 'pe', 'hdpe', 'ldpe', 'pvdf', 'ptfe', 'nylon',
                'polypropylene', 'polyethylene', 'polysulfone', 'polyphenylsulfone', 'acetal', 'delrin', 'pps',
                'polymer', 'thermoplastic', 'peek', 'rptfe', 'tfm'],
    'polymer': ['pvc', 'cpvc', 'abs', 'ppsu', 'pex', 'pp', 'pe', 'nylon', 'ptfe', 'peek'],
    'steel': ['carbon', 'stainless', 'galvanized', 'galvanised', 'alloy', 'duplex', 'chrome', '304', '316', '416',
              'a105', 'wcb'],
    'iron': ['cast', 'ductile', 'malleable', 'grey', 'gray'],
    'brass': ['dzr', 'lead', 'no-lead', 'forged', 'c27453', 'c46500', 'c69300', 'eco'],
    'bronze': ['aluminum', 'aluminium', 'silicon', 'cast', 'lead', 'no-lead', 'c84400', 'c89833'],
    'rubber': ['epdm', 'nbr', 'buna', 'fkm', 'viton', 'neoprene', 'silicone', 'hnbr', 'sbr', 'elastomer'],
    'elastomer': ['epdm', 'nbr', 'buna', 'fkm', 'viton', 'neoprene', 'silicone', 'hnbr'],
    'metal': ['steel', 'iron', 'brass', 'bronze', 'copper', 'aluminum', 'aluminium', 'stainless'],
    'threaded': ['npt', 'bspt', 'bsp', 'fnpt', 'mnpt', 'fip', 'mip', 'nptf'],
    'thread': ['npt', 'bspt', 'bsp', 'fnpt', 'mnpt', 'fip', 'mip', 'nptf'],
}


def _words(s):
    return set(re.findall(r'[a-z0-9]+(?:-[a-z0-9]+)?', str(s).lower()))


def _text_refines(specific, general):
    """True when `specific` narrows `general`: same words plus qualifiers, or a member of a material family."""
    ws, wg = _words(specific), _words(general)
    if not ws or not wg or ws == wg:
        return False
    if wg < ws:                      # "brass" -> "no-lead brass"
        return True
    for g in wg & set(MATERIAL_FAMILIES):
        if ws & set(MATERIAL_FAMILIES[g]) or any(w.startswith(tuple(MATERIAL_FAMILIES[g])) for w in ws):
            rest = wg - {g}
            if not rest or rest <= ws:
                return True
    return False


def refines(key, specific, general):
    """SPEC 6a: is spec-sheet value `specific` a more specific form of page value `general`?
    Both are spec_value-like dicts. Numbers never refine."""
    kind = SPEC_KINDS.get(key, 'text')
    sv, gv = specific.get('value'), general.get('value')
    if kind in ('set', 'cert_set', 'size_set'):
        if kind == 'cert_set':
            s_set, g_set = cert_tokens(_as_list(sv)), cert_tokens(_as_list(gv))
        elif kind == 'size_set':
            s_set = {round(x, 4) for x in (parse_size(v) for v in _as_list(sv)) if x is not None}
            g_set = {round(x, 4) for x in (parse_size(v) for v in _as_list(gv)) if x is not None}
        else:
            s_set, g_set = {norm_token(x) for x in _as_list(sv)}, {norm_token(x) for x in _as_list(gv)}
        if g_set and g_set < s_set:
            return True
        # every general item is narrowed by some specific item ("threaded" -> "NPT")
        return bool(g_set) and all(any(x == y or _text_refines(y, x) for y in _as_list(sv)) for x in _as_list(gv)) \
            and s_set != g_set
    if kind == 'text':
        return _text_refines(sv, gv)
    return False
