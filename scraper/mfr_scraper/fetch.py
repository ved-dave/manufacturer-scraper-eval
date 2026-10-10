"""Polite HTTP fetching with a disk cache that doubles as the raw store.

- robots.txt (RFC 9309) parsed for Sitemap and Crawl-delay. Disallow rules are NOT obeyed (SPEC 1a);
  each disallowed URL fetched is counted in stats['robots_overridden']
- at least MIN_DELAY_PER_HOST (or the site's Crawl-delay) between requests to one host
- retries with backoff on 429/5xx; size caps per content kind
- every response body is cached under cache/<site>/ keyed by URL, so re-runs and rule changes
  do not re-crawl (use refresh=True to bypass)
"""
import hashlib
import json
import time
from dataclasses import dataclass, field
from urllib.parse import urlsplit

import requests

from .robots import Robots
from .settings import AGENT_NAME, CACHE_DIR, MAX_BYTES, MIN_DELAY_PER_HOST, REQUEST_TIMEOUT, USER_AGENT


@dataclass
class Response:
    url: str                     # requested URL
    final_url: str
    status: int | None
    headers: dict = field(default_factory=dict)
    body: bytes = b''
    error: str | None = None
    from_cache: bool = False
    blocked_by_robots: bool = False

    @property
    def ok(self):
        return self.status == 200 and not self.error

    @property
    def sha256(self):
        return hashlib.sha256(self.body).hexdigest() if self.body else None

    @property
    def content_type(self):
        return (self.headers.get('content-type') or '').split(';')[0].strip().lower()

    def text(self):
        enc = 'utf-8'
        ct = self.headers.get('content-type') or ''
        if 'charset=' in ct:
            enc = ct.split('charset=')[-1].split(';')[0].strip() or enc
        return self.body.decode(enc, errors='replace')


class Fetcher:
    def __init__(self, site, refresh=False, log=print):
        self.site = site
        self.refresh = refresh
        self.log = log
        self.session = requests.Session()
        self.session.headers['User-Agent'] = USER_AGENT
        self.session.headers['Accept-Language'] = 'en-US,en;q=0.8'
        self.cache = CACHE_DIR / site
        self.cache.mkdir(parents=True, exist_ok=True)
        self._robots = {}
        self._last = {}
        self.stats = {'requests': 0, 'cache_hits': 0, 'robots_overridden': 0, 'errors': 0}

    # ------------------------------------------------------------- robots
    def robots(self, url):
        s = urlsplit(url)
        origin = f'{s.scheme}://{s.netloc}'
        if origin not in self._robots:
            r = self._get(origin + '/robots.txt', kind='other', check_robots=False)
            text = r.text() if r.ok else ''
            self._robots[origin] = Robots(text, AGENT_NAME)
        return self._robots[origin]

    def allowed(self, url):
        return self.robots(url).allowed(url)

    # ------------------------------------------------------------- core
    def _key(self, url, method):
        return hashlib.sha1(f'{method} {url}'.encode()).hexdigest()

    def _wait(self, host, delay):
        last = self._last.get(host)
        if last is not None:
            gap = time.monotonic() - last
            if gap < delay:
                time.sleep(delay - gap)
        self._last[host] = time.monotonic()

    def get(self, url, kind='html'):
        return self._get(url, kind)

    def head(self, url):
        return self._get(url, kind='other', method='HEAD')

    def _get(self, url, kind, method='GET', check_robots=True):
        key = self._key(url, method)
        meta_p, body_p = self.cache / f'{key}.json', self.cache / f'{key}.body'
        if not self.refresh and meta_p.exists():
            meta = json.loads(meta_p.read_text())
            self.stats['cache_hits'] += 1
            body = body_p.read_bytes() if body_p.exists() else b''
            return Response(url, meta['final_url'], meta['status'], meta['headers'], body,
                            meta.get('error'), from_cache=True, blocked_by_robots=meta.get('blocked_by_robots', False))

        if check_robots and not self.allowed(url):
            # SPEC 1a: robots.txt is not obeyed, but every overridden URL is counted and reported.
            self.stats['robots_overridden'] += 1

        host = urlsplit(url).netloc
        robots = self._robots.get(f'{urlsplit(url).scheme}://{host}')
        delay = max(MIN_DELAY_PER_HOST, (robots.crawl_delay if robots and robots.crawl_delay else 0))
        resp = None
        for attempt in range(3):
            self._wait(host, delay)
            self.stats['requests'] += 1
            try:
                r = self.session.request(method, url, timeout=REQUEST_TIMEOUT, stream=True, allow_redirects=True)
                body = b''
                if method == 'GET':
                    cap = MAX_BYTES.get(kind, MAX_BYTES['other'])
                    chunks, size = [], 0
                    for chunk in r.iter_content(65536):
                        size += len(chunk)
                        if size > cap:
                            raise ValueError(f'body exceeds {cap} bytes')
                        chunks.append(chunk)
                    body = b''.join(chunks)
                resp = Response(url, r.url, r.status_code, {k.lower(): v for k, v in r.headers.items()}, body)
                if r.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                    time.sleep(2 ** (attempt + 2))
                    continue
                break
            except (requests.RequestException, ValueError) as e:
                resp = Response(url, url, None, error=f'{type(e).__name__}: {e}')
                if attempt < 2 and not isinstance(e, ValueError):
                    time.sleep(2 ** (attempt + 1))
                    continue
                break
        if not resp.ok:
            self.stats['errors'] += 1
        keep = {k: v for k, v in resp.headers.items() if k in ('content-type', 'content-length', 'last-modified', 'etag')}
        resp.headers = keep
        if resp.status not in (200, 404, 410):
            return resp   # blocks (403/429), server errors and network failures are not cached; retry next run
        meta_p.write_text(json.dumps({'url': url, 'final_url': resp.final_url, 'status': resp.status,
                                      'headers': keep, 'error': resp.error, 'fetched_at': time.time()}))
        if resp.body:
            body_p.write_bytes(resp.body)
        return resp
