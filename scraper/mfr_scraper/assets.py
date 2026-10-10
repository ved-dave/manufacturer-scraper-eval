"""Documents, CAD, and images: classification, download, verification, best-version selection."""
import io
import re
import zipfile
from urllib.parse import unquote, urlsplit

from .settings import N, PDF_TEXT_PAGES

DOC_EXT = re.compile(r'\.(pdf|xlsx?|docx?)(?:$|\?)', re.I)
CAD_EXT = {'dwg': 'dwg', 'dxf': 'dxf', 'stp': 'step', 'step': 'step', 'igs': 'iges', 'iges': 'iges',
           'sat': 'sat', 'x_t': 'parasolid', 'x_b': 'parasolid', 'sldprt': 'solidworks', 'sldasm': 'solidworks',
           'ipt': 'inventor', 'iam': 'inventor', '3ds': '3ds', 'stl': 'stl', 'obj': 'obj', 'skp': 'sketchup',
           'rfa': 'rfa', 'rvt': 'rvt', 'ifc': 'ifc'}
BIM_FORMATS = {'rfa', 'rvt', 'ifc'}
IMAGE_EXT = re.compile(r'\.(jpe?g|png|webp|avif|gif|tiff?)(?:$|\?)', re.I)

# Ordered: first match wins. Matched against url + link text + title + first-page text.
DOC_RULES = [
    ('other_doc', r'safety data sheet|material safety|\bmsds\b'),
    ('price_list', r'price\s?list|price\s?book|list\s?price|pricelist|price\s?sheet|pricing'),
    ('submittal', r'submittal'),
    ('warranty', r'warranty|guarantee'),
    ('certificate', r'certificate|certification|declaration of conformity|\bdoc\b|letter of compliance|'
                    r'compliance (?:letter|statement|certificate)|\bwras\b|approval letter|\bnsf\b.*complian'),
    ('iom_manual', r'\biom\b|installation|install guide|instructions?|operation|maintenance|o\s?&\s?m\b|'
                   r'safety manual|user manual|owner.?s manual|\bmanual\b'),
    ('spec_sheet', r'spec(?:ification)?s?\s?sheet|data\s?sheet|datasheet|technical data|product data|'
                   r'\btds\b|[-_]ds[-_.]|[-_]ds$|cut\s?sheet|tech(?:nical)? sheet|spec(?:ification)? data|'
                   r'dimension|weights?[-_ ]dimensions|recommended[-_ ]spec|\bsrd\b|\brss\b|product sheet|\bspecs?\b'),
    ('catalog', r'catalog|catalogue|full line|product guide|selection guide|price.?catalog'),
    ('brochure', r'brochure|flyer|leaflet|overview|sell sheet|literature'),
]
PRIMARY = {'spec_sheet', 'submittal', 'price_list'}

STOPWORDS = {
    'en': 'the and of to for with is are in on be or by this that from as not all any'.split(),
    'fr': 'le la les des et du une pour avec est sont dans sur par ce cette pas tous aux'.split(),
    'es': 'el la los las y de del una para con es son en por este esta no todos al'.split(),
    'de': 'der die das und ist sind mit für von zu auf den dem nicht ein eine auch'.split(),
    'it': 'il lo la gli le e di del una per con è sono nel sul questo non tutti'.split(),
    'pt': 'o a os as e de do da uma para com é são em por este esta não todos'.split(),
    'nl': 'de het een en van voor met is zijn op door dit niet alle'.split(),
}
LANG_FILENAME = re.compile(r'(?:^|[/_\-.])(en|fr|es|de|it|pt|nl|zh|ja|ru|pl|cs)(?:[_\-.]|$)', re.I)


GENERIC_LINK_TEXT = re.compile(r'^\s*(download|view|pdf|open|click here|more|details|\d+(\.\d+)?\s?[km]b)?\s*$', re.I)


def _match_rules(hay):
    # "SDS" is a specification data sheet when it sits with spec/datasheet wording, else a safety data sheet.
    if re.search(r'\bsds\b', hay):
        return 'spec_sheet' if re.search(r'specification|datasheet|data sheet', hay) else 'other_doc'
    for doc_type, pat in DOC_RULES:
        if re.search(pat, hay):
            return doc_type
    return None


def classify_doc(url, link_text='', title='', first_page=''):
    """Strong signals first (URL path, link text, PDF title); first-page text only as a fallback."""
    path = unquote(urlsplit(url).path).lower()
    link = '' if GENERIC_LINK_TEXT.match(link_text or '') else link_text.lower()
    strong = ' '.join([path.replace('-', ' ').replace('_', ' ').replace('/', ' '), path, link, (title or '').lower()])
    return _match_rules(strong) or _match_rules(first_page[:1500].lower()) or 'other_doc'


def detect_lang(text, url=''):
    """Primary language by stopword share; 'en+fr' style when English leads with a strong second language."""
    words = re.findall(r"[a-zà-ÿ]+", text.lower())[:20000]
    if len(words) < 30:
        m = LANG_FILENAME.search(urlsplit(url).path.rsplit('/', 1)[-1])
        return (m.group(1).lower() if m else 'en'), True       # assumed
    counts = {lang: 0 for lang in STOPWORDS}
    sets = {lang: set(ws) for lang, ws in STOPWORDS.items()}
    for w in words:
        for lang, ws in sets.items():
            if w in ws:
                counts[lang] += 1
    ranked = sorted(counts.items(), key=lambda kv: -kv[1])
    (l1, c1), (l2, c2) = ranked[0], ranked[1]
    total = sum(counts.values()) or 1
    if l1 == 'en' and c2 / total >= 0.30:
        return f'en+{l2}', False
    return l1, False


def _clean_cell(c):
    return re.sub(r'\s+', ' ', c or '').strip()


def pdf_text(body, pages=PDF_TEXT_PAGES):
    """Extract text with pdfplumber (MIT). Returns (text, page_texts, title, revision_date, table_rows).

    Each page's text is its layout text followed by its table rows written as 'cell | cell | ...',
    so quotes taken from table rows appear verbatim in the saved evidence text.
    table_rows: [(page_number, [cells])]. Never raises.
    """
    try:
        import pdfplumber
        texts, rows, title = [], [], ''
        with pdfplumber.open(io.BytesIO(body)) as pdf:
            title = str((pdf.metadata or {}).get('Title') or '')
            for i, p in enumerate(pdf.pages[:pages], 1):
                try:
                    t = p.extract_text(layout=True) or ''
                except Exception:  # noqa: BLE001 - malformed pages are common
                    t = p.extract_text() or ''
                table_lines = []
                try:
                    for table in p.extract_tables():
                        for row in table:
                            cells = [_clean_cell(c) for c in row if _clean_cell(c)]
                            if len(cells) >= 2:
                                rows.append((i, cells))
                                table_lines.append(' | '.join(cells))
                except Exception:  # noqa: BLE001
                    pass
                texts.append(t + ('\n' + '\n'.join(table_lines) if table_lines else ''))
        joined = '\n'.join(texts)
        rev = None
        m = re.search(r'\b(?:rev(?:ision|\.)?|revised|date)\s*[:#]?\s*([A-Za-z]{3,9}\.?\s?\d{4}|\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}|\d{4}[-/]\d{2}(?:[-/]\d{2})?)', joined, re.I)
        if m:
            rev = m.group(1)
        return joined, texts, title, rev, rows
    except Exception:  # noqa: BLE001
        return '', [], '', None, []


def is_pdf(body):
    return body[:1024].lstrip().startswith(b'%PDF') or b'%PDF' in body[:1024]


# ------------------------------------------------------------------ CAD

def cad_from_url(url):
    path = unquote(urlsplit(url).path).lower()
    m = re.search(r'\.([a-z0-9_]+)$', path)
    ext = m.group(1) if m else ''
    if ext in CAD_EXT:
        fmt = CAD_EXT[ext]
        return {'cad_type': 'bim' if fmt in BIM_FORMATS else 'cad_file', 'formats': [fmt]}
    return None


def zip_cad_formats(body):
    try:
        names = zipfile.ZipFile(io.BytesIO(body)).namelist()
    except (zipfile.BadZipFile, OSError):
        return None
    fmts = sorted({CAD_EXT[n.rsplit('.', 1)[-1].lower()] for n in names if '.' in n and n.rsplit('.', 1)[-1].lower() in CAD_EXT})
    return fmts


def zip_name_suggests_cad(url, text=''):
    return bool(re.search(r'step|stp|cad|3d|model|dwg|dxf|revit|bim|iges|igs|drawing', unquote(url).lower() + ' ' + text.lower()))


# ------------------------------------------------------------------ images

SIZE_MARK = re.compile(r'(-\d{2,5}x\d{2,5}(?=\.\w+$))|(/styles/[^/]+/)|(/stencil/\d+x\d+/)|(_\d{2,5}x\d{0,5}(?=\.\w+$))|([?&](w|width|h|height|size|resize)=)', re.I)
CHROME_IMAGE = re.compile(r'logo|icon|sprite|favicon|social|share|badge|flag|banner|placeholder|spinner|loader|'
                          r'avatar|arrow|button|bg[-_]|background|socialmediaview|thumb(?:nail)?s?[-_/]', re.I)


NON_PRODUCT_PHOTO = re.compile(r'install(?:ation|ed|ing)?|rough[-_ ]?in|finish[-_ ]?install|lifestyle|jobsite|job[-_ ]site|'
                               r'in[-_ ]use|application[-_ ]photo|scene|environment', re.I)


def original_candidates(url):
    """Likely full-size URLs for a resized rendition (tried in order, verified by fetching)."""
    out = []
    s = urlsplit(url)
    path = s.path
    base = f'{s.scheme}://{s.netloc}'
    p2 = re.sub(r'-\d{2,5}x\d{2,5}(?=\.\w+$)', '', path)
    if p2 != path:
        out.append(base + re.sub(r'(\.\w+)$', r'-scaled\1', p2))
        out.append(base + p2)
    p3 = re.sub(r'/styles/[^/]+/public/', '/', path)
    if p3 != path:
        out.append(base + re.sub(r'(\.(?:jpe?g|png))\.webp$', r'\1', p3, flags=re.I))
    p4 = re.sub(r'/stencil/\d+x\d+/', '/stencil/original/', path)
    if p4 != path:
        out.append(base + p4 + (('?' + s.query) if s.query else ''))
    return out


def rank_candidate(url, declared_width):
    """Higher is better: no size marker beats resized; then larger declared width."""
    resized = bool(SIZE_MARK.search(url))
    return (0 if resized else 1, declared_width or 0, len(url) * -1)


def image_dims_phash(body):
    try:
        from PIL import Image
        import imagehash
        im = Image.open(io.BytesIO(body))
        w, h = im.size
        ph = str(imagehash.phash(im.convert('RGB')))
        return w, h, ph
    except Exception:  # noqa: BLE001 - corrupt/unsupported images are skipped
        return None, None, None


def image_type_of(url, alt=''):
    hay = (unquote(url) + ' ' + alt).lower()
    if re.search(r'drawing|dimension|dimensional|\bdim\b|[-_]d\.(png|jpe?g)|schematic|diagram|cross[- ]section|exploded', hay):
        return 'dimensional_drawing'
    return 'product_photo'
