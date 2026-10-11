"""Fetcher for the processing layer: one polite queue per host, run in parallel across hosts.

- requests to one host stay serialised at MIN_DELAY_PER_HOST (per-host lock); different hosts run concurrently
- a response that is not cached (blocked, error) is remembered for the run and never retried
- a host that blocks BLOCK_STREAK requests in a row is not asked again in this run (recorded as host_blocked)
- requests are counted per purpose ('page' = the cost of not having found_on/html_snapshot, 'asset')
"""
import collections
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit

import requests

from ..fetch import Fetcher, Response
from ..settings import USER_AGENT

BLOCK_STATUS = {401, 403, 429}
BLOCK_BODY = re.compile(rb'captcha|cf-chl|challenge-platform|just a moment\.\.\.|access denied|attention required', re.I)
BLOCK_STREAK = 8


def is_blocked(resp):
    if resp.status in BLOCK_STATUS:
        return True
    # bot walls often answer 200/503 with a small challenge page
    return (resp.status in (200, 503) and 'html' in (resp.content_type or '') and len(resp.body) < 60_000
            and bool(BLOCK_BODY.search(resp.body[:60_000])))


class HostQueueFetcher(Fetcher):
    def __init__(self, site, cache_name=None, refresh=False, log=print, offline=False):
        self._local = threading.local()
        super().__init__(cache_name or site, refresh=refresh, log=log)
        self.offline = offline
        self._locks = collections.defaultdict(threading.RLock)
        self._locks_guard = threading.Lock()
        self._stats_lock = threading.Lock()
        self._memo = {}
        self._streak = collections.Counter()
        self.blocked_hosts = {}
        self.purpose_stats = collections.Counter()
        self.blocked = []            # (url, status/reason)

    # one requests.Session per thread
    @property
    def session(self):
        s = getattr(self._local, 'session', None)
        if s is None:
            s = self._local.session = requests.Session()
            s.headers['User-Agent'] = USER_AGENT
            s.headers['Accept-Language'] = 'en-US,en;q=0.8'
        return s

    @session.setter
    def session(self, value):
        pass

    def _lock(self, host):
        with self._locks_guard:
            return self._locks[host]

    def get(self, url, kind='html', purpose=None):
        host = urlsplit(url).netloc
        key = (url, 'GET')
        if key in self._memo:
            return self._memo[key]
        if host in self.blocked_hosts:
            return Response(url, url, None, error=f'host_blocked: {self.blocked_hosts[host]}')
        if self.offline and not (self.cache / f'{self._key(url, "GET")}.json').exists():
            return Response(url, url, None, error='offline: not in cache')
        with self._lock(host):
            if key in self._memo:
                return self._memo[key]
            before = self.stats['requests']
            r = self._get(url, kind)
            made = self.stats['requests'] - before
        with self._stats_lock:
            if made:
                self.purpose_stats[purpose or kind] += made
            if not r.from_cache and is_blocked(r):
                self.blocked.append((url, r.status or r.error))
                self._streak[host] += 1
                if self._streak[host] >= BLOCK_STREAK:
                    self.blocked_hosts[host] = f'{BLOCK_STREAK} blocked responses in a row (last {r.status})'
                    self.log(f'  host {host} is blocking automated requests; not asking it again this run')
            elif not r.from_cache and r.status:
                self._streak[host] = 0
            if not r.from_cache and r.status not in (200, 404, 410):
                self._memo[key] = r
        return r

    def response_blocked(self, r):
        return is_blocked(r) or (r.error or '').startswith('host_blocked')

    def prefetch(self, items, workers=8):
        """items: [(url, kind, purpose)]. Warms the cache with one worker per host (hosts run in parallel)."""
        by_host = collections.OrderedDict()
        for u, kind, purpose in dict.fromkeys(items):
            by_host.setdefault(urlsplit(u).netloc, []).append((u, kind, purpose))

        def drain(host_items):
            for u, kind, purpose in host_items:
                try:
                    self.get(u, kind, purpose)
                except Exception as e:   # noqa: BLE001  (prefetch is best effort; the main pass records failures)
                    self.log(f'  prefetch error {u}: {type(e).__name__}: {e}')

        with ThreadPoolExecutor(max_workers=max(1, min(workers, len(by_host)))) as ex:
            list(ex.map(drain, by_host.values()))


class AssetPrefetcher:
    """Background cache warming while pages are still loading: one worker thread per asset host."""

    def __init__(self, fetcher):
        import queue
        self._queue_cls = queue.Queue
        self.fetcher = fetcher
        self.queues, self.threads, self.seen = {}, [], set()
        self.lock = threading.Lock()

    def submit(self, url, kind, purpose='asset'):
        host = urlsplit(url).netloc
        with self.lock:
            if url in self.seen:
                return
            self.seen.add(url)
            q = self.queues.get(host)
            if q is None:
                q = self.queues[host] = self._queue_cls()
                t = threading.Thread(target=self._work, args=(q,), daemon=True)
                t.start()
                self.threads.append(t)
        q.put((url, kind, purpose))

    def _work(self, q):
        while True:
            item = q.get()
            if item is None:
                return
            try:
                self.fetcher.get(*item)
            except Exception as e:   # noqa: BLE001  (best effort; the main pass records failures)
                self.fetcher.log(f'  prefetch error {item[0]}: {type(e).__name__}: {e}')

    def close(self):
        for q in self.queues.values():
            q.put(None)
        for t in self.threads:
            t.join()
