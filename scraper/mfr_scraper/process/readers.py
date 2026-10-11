"""Readers for Layer 1 link files. Both return the same LinkSet so one processing path serves both levels.

- L0: the old agent's flat CSV (url,url_type). Pages and assets with no relationships between them.
- L1: the enriched JSONL of OLD_AGENT_IMPROVEMENTS.md: `page` records (HTTP and page facts, html_snapshot)
  and `link` records (one per link per page, with found_on/link_text/section/in_chrome/...).
"""
import csv
import json
from dataclasses import dataclass, field
from pathlib import Path

L0_TYPES = {'site_page': 'page', 'page': 'page', 'pdf': 'pdf', 'document': 'other', 'image': 'image', 'bim': 'bim',
            'cad': 'cad', 'archive': 'archive', 'spreadsheet': 'spreadsheet', 'video': 'video'}


@dataclass
class PageFacts:
    url: str
    status: int | None = None
    final_url: str | None = None
    content_type: str | None = None
    page_title: str | None = None
    h1: str | None = None
    breadcrumb: list | None = None
    canonical_url: str | None = None
    lang: str | None = None
    hreflang: dict | None = None
    jsonld_product: dict | None = None
    has_spec_table: bool | None = None
    n_links_same_section: int | None = None
    meta_description: str | None = None
    html_snapshot: str | None = None      # resolved absolute path
    last_modified: str | None = None
    etag: str | None = None


@dataclass
class LinkFacts:
    url: str
    url_type: str
    found_on: str | None = None
    link_text: str | None = None
    section: str | None = None
    in_chrome: bool | None = None
    link_kind: str | None = None
    status: int | None = None
    final_url: str | None = None
    content_type: str | None = None
    alt: str | None = None
    width: int | None = None
    height: int | None = None
    srcset: list = field(default_factory=list)
    wrapping_link: str | None = None


@dataclass
class LinkSet:
    level: str                       # 'L0' | 'L1'
    path: str
    pages: dict                      # url -> PageFacts (in file order)
    links: list                      # [LinkFacts]
    skipped: list = field(default_factory=list)   # (row, reason) for malformed input rows

    def assets(self):
        return [l for l in self.links if l.url_type != 'page']

    def links_on(self):
        """found_on -> [LinkFacts] (L1 only; empty for L0)."""
        out = {}
        for l in self.links:
            if l.found_on:
                out.setdefault(l.found_on, []).append(l)
        return out


def read_l0(path):
    pages, links, skipped = {}, [], []
    with open(path, newline='') as f:
        for i, row in enumerate(csv.DictReader(f), 2):
            url, raw_type = (row.get('url') or '').strip(), (row.get('url_type') or '').strip()
            kind = L0_TYPES.get(raw_type)
            if not url.startswith(('http://', 'https://')) or kind is None:
                skipped.append((i, f'malformed row (url_type={raw_type!r})'))
                continue
            if kind == 'page':
                pages.setdefault(url, PageFacts(url=url))
            else:
                links.append(LinkFacts(url=url, url_type=kind))
    return LinkSet('L0', str(path), pages, links, skipped)


def read_l1(path):
    path = Path(path)
    pages, links, skipped = {}, [], []
    page_fields = set(PageFacts.__dataclass_fields__)
    link_fields = set(LinkFacts.__dataclass_fields__)
    with open(path) as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                skipped.append((i, 'not JSON'))
                continue
            if rec.get('record') == 'page':
                p = PageFacts(**{k: v for k, v in rec.items() if k in page_fields})
                if p.html_snapshot and not p.html_snapshot.startswith(('s3://', 'gs://', 'http')):
                    p.html_snapshot = str((path.parent / p.html_snapshot).resolve())
                pages[p.url] = p
            elif rec.get('record') == 'link':
                l = LinkFacts(**{k: v for k, v in rec.items() if k in link_fields})
                l.srcset = list(l.srcset or [])
                links.append(l)
            else:
                skipped.append((i, f'unknown record {rec.get("record")!r}'))
    return LinkSet('L1', str(path), pages, links, skipped)


def read_links(path, level=None):
    """level: 'L0', 'L1' or None (by extension: .csv = L0, otherwise L1)."""
    level = level or ('L0' if str(path).lower().endswith('.csv') else 'L1')
    return read_l0(path) if level == 'L0' else read_l1(path)
