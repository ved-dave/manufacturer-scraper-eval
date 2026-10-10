"""robots.txt per RFC 9309.

Python's urllib.robotparser ignores `*`/`$` wildcards and does not merge multiple groups for the
same user-agent, so it would (for example) allow PDFs on a site whose robots.txt says
`User-agent: *` / `Disallow: *.pdf` in a second group. This parser:
  - merges every group whose user-agent matches (specific token preferred over `*`)
  - supports `*` and `$` in paths
  - picks the longest matching rule; Allow wins ties
"""
import re
from urllib.parse import urlsplit, unquote


class Robots:
    def __init__(self, text, agent_token):
        self.agent = agent_token.lower()
        self.rules = []          # (allow: bool, pattern: str)
        self.sitemaps = []
        self.crawl_delay = None
        self._parse(text or '')

    def _parse(self, text):
        groups = []              # [(agents:set, rules:list, delay)]
        agents, rules, delay, in_rules = set(), [], None, False
        for raw in text.splitlines():
            line = raw.split('#', 1)[0].strip()
            if ':' not in line:
                continue
            key, val = (x.strip() for x in line.split(':', 1))
            key = key.lower()
            if key == 'sitemap':
                if val:
                    self.sitemaps.append(val)
                continue
            if key == 'user-agent':
                if in_rules:
                    groups.append((agents, rules, delay))
                    agents, rules, delay, in_rules = set(), [], None, False
                agents.add(val.lower())
            elif key in ('allow', 'disallow'):
                in_rules = True
                if val:
                    rules.append((key == 'allow', val))
            elif key == 'crawl-delay':
                in_rules = True
                try:
                    delay = float(val)
                except ValueError:
                    pass
        if agents:
            groups.append((agents, rules, delay))

        specific = [g for g in groups if any(a != '*' and a == self.agent for a in g[0])]
        chosen = specific or [g for g in groups if '*' in g[0]]
        for _, r, d in chosen:
            self.rules.extend(r)
            if d is not None:
                self.crawl_delay = max(self.crawl_delay or 0, d)

    @staticmethod
    def _to_regex(pattern):
        anchored = pattern.endswith('$')
        body = pattern[:-1] if anchored else pattern
        rx = ''.join('.*' if ch == '*' else re.escape(ch) for ch in body)
        return re.compile(rx + ('$' if anchored else ''))

    def allowed(self, url):
        s = urlsplit(url)
        path = unquote(s.path or '/') + (('?' + s.query) if s.query else '')
        best_len, best_allow = -1, True
        for allow, pattern in self.rules:
            p = pattern if pattern.startswith(('/', '*')) else '/' + pattern
            if self._to_regex(p).match(path):
                length = len(pattern)
                if length > best_len or (length == best_len and allow):
                    best_len, best_allow = length, allow
        return best_allow
