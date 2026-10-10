"""Map spec labels to schema fields and parse raw values into the schema's value shapes.

Site-agnostic: works on any "label -> value" pair, whether it came from an HTML table, a
definition list, a div pair, or a "Label: value" line in a PDF.
"""
import re

from .settings import N

# Longest synonym wins, so "seat material" beats "material".
FIELD_LABELS = {
    'size_range': ['size range', 'sizes', 'size', 'nominal size', 'pipe size', 'valve size', 'available sizes',
                   'nominal pipe size', 'nps', 'dimensions available', 'connection size'],
    'material_body': ['body material', 'body materials', 'body', 'material', 'materials', 'construction',
                      'body construction', 'housing material'],
    'material_trim': ['trim', 'trim material', 'disc', 'disc material', 'disc materials', 'ball', 'ball material',
                      'wedge', 'plug material', 'trim materials'],
    'material_seat': ['seat', 'seat material', 'seat materials', 'seats', 'liner', 'liner material', 'seat/liner'],
    'material_seals': ['seal', 'seals', 'seal material', 'o-ring', 'o-rings', 'o ring', 'packing', 'gasket',
                       'stem seal', 'elastomer', 'elastomers'],
    'end_connections': ['end connection', 'end connections', 'connection', 'connections', 'ends', 'end type',
                        'end style', 'connection type', 'end connection type', 'inlet/outlet', 'connection style',
                        'body style', 'end'],
    'pressure_rating': ['pressure rating', 'maximum allowable operating pressure', 'max pressure',
                        'maximum pressure', 'working pressure', 'max working pressure', 'operating pressure',
                        'pressure', 'cwp', 'wog', 'rated pressure', 'maximum operating pressure', 'pressure class',
                        'max. pressure', 'pressure range'],
    'temperature_range': ['temperature range', 'temperature', 'operating temperature', 'temp range', 'temp',
                          'max temperature', 'maximum temperature', 'service temperature', 'temperature rating',
                          'max. temperature', 'operating temperature range'],
    'certifications': ['certifications', 'certification', 'approvals', 'approval', 'listings', 'agency listings',
                       'listed', 'certified', 'approvals/listings', 'compliance'],
    'standards': ['standards', 'standard', 'design standard', 'conforms to', 'specifications met',
                  'applicable standards', 'manufacturing standard', 'face to face'],
    'applications': ['applications', 'application', 'uses', 'recommended use', 'suitable for', 'service',
                     'media', 'typical applications', 'ideal for', 'markets', 'industries'],
    # Recognised so they are NOT mistaken for a scored field; kept in additional_specs.
    '_other': ['stem', 'stem material', 'stem materials', 'shaft', 'shaft material', 'actuator', 'actuation',
               'operator', 'weight', 'cv', 'flow coefficient', 'bolting', 'spring', 'spring material',
               'handle', 'handle material', 'finish', 'coating', 'color', 'colour', 'model', 'model number',
               'part number', 'sku', 'upc', 'warranty', 'country of origin', 'packaging', 'quantity'],
}
_SYN = sorted(((s, f) for f, syns in FIELD_LABELS.items() for s in syns), key=lambda x: -len(x[0]))


def clean_label(label):
    return re.sub(r'\s+', ' ', re.sub(r'[:*()•]', ' ', label)).strip().lower()


def field_for_label(label):
    lab = clean_label(label)
    if not lab or len(lab) > 60:
        return None
    words = len(lab.split())
    for syn, f in _SYN:
        if lab == syn:
            return f
    # Allow light qualifiers ("Size Range (in)", "Max Working Pressure") but not long headings.
    for syn, f in _SYN:
        if words <= len(syn.split()) + 2 and (lab.startswith(syn + ' ') or lab.endswith(' ' + syn)):
            return f
    return None


# ------------------------------------------------------------------ value parsers

FRACTION = r'\d+(?:[-\s]\d+/\d+)?(?:/\d+)?(?:\.\d+)?'


def _sizes_inch(text):
    """Inch/NPS size tokens in order of appearance."""
    t = text.replace('″', '"').replace('”', '"').replace("''", '"')
    toks = []
    for m in re.finditer(r'(?:nps\s*)?(' + FRACTION + r')\s*(?:"|in\b|inch(?:es)?\b)?', t, re.I):
        raw = m.group(1).strip()
        context = t[max(0, m.start() - 4):m.end() + 6].lower()
        if 'dn' in context[:4] or 'mm' in context[-6:]:
            continue
        if N.parse_size(raw) is not None:
            toks.append(raw.replace(' ', '-') if re.fullmatch(r'\d+\s\d+/\d+', raw) else raw)
    return toks


def parse_size_range(raw):
    t = raw.strip()
    if len(re.findall(r'\d+', t)) > 8:          # chart axis / table row, not a size statement
        return None
    unit = 'NPS' if re.search(r'\bnps\b', t, re.I) else 'in'
    dn_only = re.search(r'\bdn\s*\d', t, re.I) and not re.search(r'nps|"|\bin\b|inch|\d/\d', t, re.I)
    if dn_only:
        nums = [x for x in re.findall(r'\d+', t)]
        return ({'min': nums[0], 'max': nums[-1]}, 'DN') if nums else None
    # Take the inch part before any metric alternative ("NPS 22 to 120 / DN 550 to 3000").
    inch_part = re.split(r'\(|/\s*dn|\bdn\b', t, flags=re.I)[0]
    toks = _sizes_inch(inch_part)
    if not toks:
        return None
    vals = sorted(toks, key=N.parse_size)
    if N.parse_size(vals[-1]) > 200 or N.parse_size(vals[0]) <= 0:   # beyond any valve/pipe size in inches
        return None
    return {'min': vals[0], 'max': vals[-1]}, unit


def parse_sizes_available(raw):
    if not re.search(r'[,;]', raw):
        return None
    toks = _sizes_inch(re.split(r'\(|/\s*dn|\bdn\b', raw, flags=re.I)[0])
    return list(dict.fromkeys(toks)) if len(toks) >= 3 else None


def parse_pressure(raw):
    t = raw.replace(',', '')
    cond = re.search(r'\b(WOG|CWP|WSP|SWP|WWP)\b', t)
    hits = [(float(v), u.lower().replace('psig', 'psi')) for v, u in re.findall(r'(\d+(?:\.\d+)?)\s*(psig|psi|bar|kpa)\b', t, re.I)]
    if hits:
        # Several ratings (e.g. per series): report the highest, in the unit it was stated in.
        unit = 'psi' if any(u == 'psi' for _, u in hits) else hits[0][1]
        same = [v for v, u in hits if u == unit]
        return max(same), unit, (cond.group(1) if cond else None)
    m = re.search(r'\b(\d+(?:\.\d+)?)\s*(WOG|CWP|WSP|SWP|WWP)\b', t)
    if m:
        return float(m.group(1)), 'psi', m.group(2)
    m = re.search(r'\bPN\s?(\d+)\b', t, re.I)
    if m:
        return float(m.group(1)), 'bar', f'PN{m.group(1)}'
    m = re.search(r'\bclass\s?(\d{3,4})\b', t, re.I)
    if m:
        return None  # ASME class is not a single pressure; leave for raw/additional specs
    return None


def parse_temperature(raw):
    t = raw.replace('º', '°').replace('−', '-').replace('–', '-')
    for unit in ('F', 'C'):
        ms = list(re.finditer(r'(-?)\s?(\d+(?:\.\d+)?)\s*°?\s*' + unit + r'\b', t))
        vals = []
        for i, m in enumerate(ms):
            v = float(m.group(2))
            # "0F -123F": a dash right after a previous reading is a range separator, not a sign.
            separator = i > 0 and t[ms[i - 1].end():m.start()].strip() == ''
            vals.append(-v if m.group(1) and not separator else v)
        if len(vals) >= 2:
            return {'min': min(vals[:2]), 'max': max(vals[:2])}, unit
        if len(vals) == 1:
            if re.search(r'\bmax|up to|maximum|<', t, re.I):
                return {'min': None, 'max': vals[0]}, unit
            return {'min': None, 'max': vals[0]}, unit
    return None


CONNECTION_WORDS = [
    (r'\bnpt\b|national pipe thread', 'NPT'), (r'\bbspt?\b|bs en 10226|iso 7-1|bs 21\b', 'BSPT'),
    (r'\bthread(?:ed)?\b|\bfip\b|\bmip\b', 'threaded'), (r'solder|sweat|\bc\s?x\s?c\b', 'solder'),
    (r'\bpress\b|propress|press[- ]fit', 'press'), (r'\bpex\b|f1807|f1960|f2159|f2080', 'PEX'),
    (r'groov', 'grooved'), (r'flang', 'flanged'), (r'\bwafer\b', 'wafer'), (r'\blug(?:ged)?\b', 'lug'),
    (r'butt[- ]?weld', 'butt weld'), (r'socket[- ]?weld', 'socket weld'), (r'compression', 'compression'),
    (r'push[- ]?(?:fit|to[- ]connect)|\bpdq\b', 'push-fit'), (r'\bcrimp', 'crimp'), (r'\bunion\b', 'union'),
    (r'\bflare\b', 'flare'), (r'\bhose\b', 'hose'), (r'\bsolvent\b|\bsocket\b(?! weld)', 'solvent weld'),
    (r'\bno[- ]hub\b', 'no-hub'), (r'\bhub\b', 'hub'), (r'\bspigot\b', 'spigot'), (r'\bcamlock|cam\s?&\s?groove', 'cam & groove'),
]


def parse_connections(raw):
    found = [c for pat, c in CONNECTION_WORDS if re.search(pat, raw, re.I)]
    if 'NPT' in found or 'BSPT' in found:
        found = [c for c in found if c != 'threaded']
    return list(dict.fromkeys(found)) or None


STANDARD_RX = re.compile(
    r'\b(?:ASME|ANSI|ASTM|MSS|API|AWWA|ASSE|ISO|BS EN|EN|BS|CSA|DIN|IAPMO|IGC|PDI|ASPE)'
    r'(?:/ANSI)?\s?(?:SP-?|[A-Z]\s?)?\d[\w.\-/]*(?:\s?(?:Class|Type)\s?\d+)?', re.I)


def parse_standards(raw):
    vals = [re.sub(r'\s+', ' ', m.group(0)).strip() for m in STANDARD_RX.finditer(raw)]
    vals = [v for v in vals if not re.match(r'(?i)nsf', v)]
    return list(dict.fromkeys(vals)) or None


def parse_certifications(raw):
    out = []
    for pat, canon in N.CERT_PATTERNS:
        if re.search(pat, raw, re.I):
            out.append(canon)
    if re.search(r'nsf', raw, re.I) and re.search(r'\b372\b', raw) and 'NSF/ANSI 372' not in out:
        out.append('NSF/ANSI 372')   # "NSF 61/372", "NSF/ANSI/CAN 61 & 372"
    for m in re.finditer(r'\b(ASSE\s?\d{4}|cUPC|UPC|WRAS|ACS|KIWA|DVGW|ABS|CE|ATEX|PED|DNV|SIL\s?\d?|'
                         r'Bureau Veritas|Lloyd\'s Register|Watermark|ENERGY STAR|CRN)\b', raw):
        out.append(m.group(1).strip())
    return list(dict.fromkeys(out)) or None


def parse_list(raw):
    parts = [p.strip(' .') for p in re.split(r'[,;\n•]|\band\b', raw) if p.strip(' .')]
    parts = [p for p in parts if 1 < len(p) < 60]
    return parts or None


HEADING_WORDS = re.compile(r'\b(materials?|factor|description|qty|quantity|item|part|no\.|number|notes?|'
                           r'dimensions?|weights?|series|model|options?|features?)\s*$', re.I)


def parse_field(field, raw):
    """Return (value, unit, conditions) for a raw label value, or None if it cannot be parsed."""
    raw = re.sub(r'\s+', ' ', raw or '').strip()
    if not raw or len(raw) > 400:
        return None
    # A value that is itself a column heading ("O-Ring Materials", "Factor") is not a value.
    if (field_for_label(raw) and not re.search(r"\d", raw)) or (HEADING_WORDS.search(raw) and len(raw.split()) <= 3):
        return None
    if field == 'size_range':
        r = parse_size_range(raw)
        return (r[0], r[1], None) if r else None
    if field == 'sizes_available':
        v = parse_sizes_available(raw)
        return (v, 'in', None) if v else None
    if field == 'pressure_rating':
        r = parse_pressure(raw)
        return (r[0], r[1], r[2]) if r else None
    if field == 'temperature_range':
        r = parse_temperature(raw)
        return (r[0], r[1], None) if r else None
    if field == 'end_connections':
        v = parse_connections(raw)
        return (v, None, None) if v else None
    if field == 'certifications':
        v = parse_certifications(raw)
        return (v, None, None) if v else None
    if field == 'standards':
        v = parse_standards(raw)
        return (v, None, None) if v else None
    if field == 'applications':
        if len(raw.split()) < 2 and ',' not in raw:     # single words in PDFs are usually table headers
            return None
        v = parse_list(raw)
        return (v, None, None) if v else None
    if field.startswith('material_'):
        # Short material lists only; prose descriptions are not values.
        is_sentence = bool(re.search(r'[a-z]\.\s+[A-Z]', raw)) or raw.rstrip().endswith('.') and len(raw.split()) > 8
        is_list = raw.count(',') >= 1 and not is_sentence
        if is_sentence or (not is_list and (len(raw) > 120 or len(raw.split()) > 16)) or len(raw) > 300:
            return None
        return (raw, None, None)
    return None


# ------------------------------------------------------------------ PDF text

LINE_LABEL_RX = re.compile(r'^\s*([A-Za-z][A-Za-z /&.\-()]{1,45}?)\s*(?::|\.{3,}|\s{2,}|\t)\s*(\S.{0,300})$')


def pairs_from_text(text):
    """'Label: value' style pairs from PDF text (layout mode keeps 2+ spaces between columns)."""
    out = []
    for line in text.splitlines():
        m = LINE_LABEL_RX.match(line)
        if not m:
            continue
        label, value = m.group(1).strip(), m.group(2).strip()
        f = field_for_label(label)
        if f:
            out.append((label, value, f, line.strip()))
    return out


def scan_text_for_lists(text):
    """Certifications/standards mentioned anywhere (e.g. in an approvals paragraph)."""
    out = {}
    for f, parser in (('certifications', parse_certifications), ('standards', parse_standards)):
        hits = []
        for line in text.splitlines():
            v = parser(line)
            if v:
                hits.append((v, line.strip()))
        if hits:
            out[f] = hits
    return out
