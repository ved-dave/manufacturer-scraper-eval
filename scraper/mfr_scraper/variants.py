"""Orderable items (SPEC 3: a variant has its own manufacturer identifier) from model/part-number tables.

Two layouts are common on manufacturer pages and spec sheets:
- a row labelled with an identifier heading followed by the identifiers ("Model #  A1  A2  A3");
- a table with an identifier column ("Part No. | Size | ...") whose rows are the orderable items.
Parts lists ("Item | Description | Material | Qty") are not variants: a bare "Item"/"Part" heading is not enough.
"""
import re

ID_LABEL = re.compile(
    r'(?:\bmodel|\bpart|\bcatalog(?:ue)?|\bcat\.|\bitem|\border(?:ing)?|\bproduct|\barticle|\bstock)\s*'
    r'(?:no\.?|nos\.?|numbers?|#|codes?|ids?)'
    r'|\bmodels?\b(?!\s+(?:series|shown|type|description))|\bskus?\b|\bupc\b', re.I)
ID_TOKEN = re.compile(r'^(?=[^\s]*\d)[A-Z0-9][A-Z0-9\-./]{1,24}$', re.I)
UNIT_TOKEN = re.compile(r'^\d+(?:[./-]\d+)*(?:mm|in|"|lbs?|kg|psi|bar|°[fc]|ft|cm|%)?$', re.I)
SIZE_HEAD = re.compile(r'\b(size|nps|dn|diameter|dimension)\b', re.I)


def _is_label(cell):
    c = cell.strip().rstrip(':').strip()
    return bool(c) and len(c) <= 30 and ID_LABEL.fullmatch(c) is not None


def _is_id(tok):
    tok = tok.strip().strip(',;')
    if not ID_TOKEN.match(tok):
        return False
    if re.fullmatch(r'\d+', tok):
        return len(tok) >= 3          # bare numbers: item counts and sizes are short
    return not UNIT_TOKEN.match(tok) or bool(re.search(r'[A-Z]', tok, re.I))


def from_rows(rows):
    """rows: list of cell lists (HTML or PDF table rows) -> [(sku, size, quote)]."""
    out = []
    header, id_col, size_col = None, None, None
    for cells in rows:
        cells = [c.strip() for c in cells if c and c.strip()]
        if not cells:
            continue
        # row layout: label cell then identifiers
        if _is_label(cells[0]) and len(cells) >= 3 and all(_is_id(c) for c in cells[1:]):
            out += [(c.strip(), None, ' | '.join(cells)) for c in cells[1:]]
            header = None
            continue
        # column layout: a header row with an identifier column
        labels = [i for i, c in enumerate(cells) if _is_label(c)]
        if labels and len(cells) >= 2 and not any(_is_id(c) for c in cells):
            header, id_col = cells, labels[0]
            size_col = next((i for i, c in enumerate(cells) if SIZE_HEAD.search(c)), None)
            continue
        if header and len(cells) == len(header) and _is_id(cells[id_col]):
            size = cells[size_col] if size_col is not None else None
            out.append((cells[id_col], size, ' | '.join(cells)))
        elif header and len(cells) != len(header):
            header = None
    # a column of fewer than two items is more likely a single reference than a variant table
    return out if len(out) >= 2 else []


LINE_LABEL = re.compile(r'((?:model|part|catalog|cat\.|item|order(?:ing)?|product|article|stock)\s*(?:no\.?|nos\.?|numbers?|#|codes?)'
                        r'|\bmodels?|\bskus?)\s*:?\s+((?:[A-Z0-9][A-Z0-9\-./]{1,24}[,;]?\s+){1,}[A-Z0-9][A-Z0-9\-./]{1,24})\s*$', re.I)


def from_lines(text):
    """'Model #  SRH1  SRH2  SRH3' lines, or a 'Models' heading line followed by '201, 203, 205', -> [(sku, None, quote)]."""
    out = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for i, line in enumerate(lines):
        m = LINE_LABEL.search(line)
        if m:
            toks = [t for t in re.split(r'[,;\s]+', m.group(2)) if t]
            if len(toks) >= 2 and all(_is_id(t) for t in toks):
                out += [(t, None, line) for t in toks]
            continue
        if _is_label(line) and i + 1 < len(lines):
            toks = [t for t in re.split(r'[,;\s]+', lines[i + 1]) if t]
            if len(toks) >= 2 and all(_is_id(t) for t in toks):
                out += [(t, None, lines[i + 1]) for t in toks]
    return out
