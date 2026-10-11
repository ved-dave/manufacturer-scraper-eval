"""Parsed-PDF cache: each PDF is parsed once, keyed by its content hash.

Only the extracted result (text, page texts, title, revision date, table rows) is kept, never the PDF body or
parser objects. Results are stored on disk under cache/parsed-pdf/, so memory stays flat however large the site
is and re-runs skip parsing; a small in-memory LRU, capped in bytes, serves repeats within a run.
"""
import collections
import json
import os

from . import assets as A
from .settings import CACHE_DIR, PDF_PARSE_MEM_BYTES, PDF_TEXT_PAGES

PARSER_VERSION = 1   # bump when assets.pdf_text changes what it returns


def _size(result):
    text, pages, title, rev, rows = result
    return len(text) + sum(map(len, pages)) + len(title) + sum(len(c) for _, cells in rows for c in cells)


class ParsedPdfCache:
    def __init__(self, root=None, mem_cap=PDF_PARSE_MEM_BYTES, pages=PDF_TEXT_PAGES, parse=None):
        self.dir = (root or CACHE_DIR / 'parsed-pdf') / f'v{PARSER_VERSION}-p{pages}'
        self.mem_cap, self.pages = mem_cap, pages
        self.parse = parse or A.pdf_text
        self.mem = collections.OrderedDict()
        self.mem_bytes = 0
        self.stats = {'parsed': 0, 'disk_hits': 0, 'mem_hits': 0, 'evicted': 0}

    def get(self, sha256, body):
        if sha256 in self.mem:
            self.mem.move_to_end(sha256)
            self.stats['mem_hits'] += 1
            return self.mem[sha256]
        path = self.dir / sha256[:2] / f'{sha256}.json'
        result = self._load(path)
        if result is None:
            result = self.parse(body, pages=self.pages)
            self.stats['parsed'] += 1
            self._store(path, result)
        else:
            self.stats['disk_hits'] += 1
        self._remember(sha256, result)
        return result

    def _load(self, path):
        try:
            text, pages, title, rev, rows = json.loads(path.read_text(encoding='utf-8'))
            return text, pages, title, rev, [(pg, cells) for pg, cells in rows]
        except (OSError, ValueError, TypeError):
            return None   # missing or unreadable entry: parse again

    def _store(self, path, result):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(f'.{os.getpid()}.tmp')
            tmp.write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
            os.replace(tmp, path)
        except OSError:
            pass   # the cache is an optimisation; a failed write must not fail the run

    def _remember(self, key, result):
        size = _size(result)
        if size > self.mem_cap:
            return
        self.mem[key] = result
        self.mem_bytes += size
        while self.mem_bytes > self.mem_cap:
            _, old = self.mem.popitem(last=False)
            self.mem_bytes -= _size(old)
            self.stats['evicted'] += 1
