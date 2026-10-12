"""Phase 3 resolver, level 1: answer unsure items from stored evidence.

Reads the unsure records of a process run (<site>.decisions.jsonl), asks a model one question per record using
only the stored page snapshots, and keeps an answer only when its quotes are found verbatim in those snapshots.
Answers are cached by question + evidence hash, so a question is never paid for twice. Answer keys are never read.
Writes <site>.resolutions.jsonl; `process --resolutions` applies the verified answers.
"""
import hashlib
import json
import os
import re
import time
from pathlib import Path

from .. import page as P
from .fetching import HostQueueFetcher

PROMPT_VERSION = 'fg-1'
KINDS = ('family_grouping',)
MAX_CHARS = 6000
PROMPT = """You decide whether two manufacturer product pages describe the SAME product family (one product sold in
several sizes, connections, finishes or options) or DIFFERENT products. Use only the page text below.

Question: {question}

=== PAGE A: {url_a}
{text_a}

=== PAGE B: {url_b}
{text_b}

Reply with one JSON object and nothing else:
{{"answer": "same" | "different" | "unsure",
  "quote_a": "<short text copied exactly from PAGE A that supports the answer>",
  "quote_b": "<short text copied exactly from PAGE B that supports the answer>",
  "reason": "<one sentence>"}}
Answer "unsure" if the text does not settle it."""


def _ws(s):
    return re.sub(r'\s+', ' ', s or '').strip().lower()


def quote_ok(quote, text):
    q = _ws(quote)
    return len(q) >= 3 and q in _ws(text)


def page_text(fetcher, url):
    r = fetcher.get(url, kind='html', purpose='page')
    if not r.body:
        return None
    return P.visible_text(P.soup_of(r.body.decode('utf-8', 'replace')))[:MAX_CHARS]


def questions(decisions_path, kinds=KINDS):
    seen = set()
    with open(decisions_path) as f:
        lines = f.readlines()
    for line in lines:
        d = json.loads(line)
        if d.get('decision') == 'unsure' and d.get('unsure_kind') in kinds and d['cache_key'] not in seen:
            seen.add(d['cache_key'])
            yield d


def anthropic_backend(model, api_key=None):
    import requests
    key = api_key or os.environ['ANTHROPIC_API_KEY']

    def ask(prompt):
        for attempt in range(5):
            r = requests.post('https://api.anthropic.com/v1/messages', timeout=120,
                              headers={'x-api-key': key, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'},
                              json={'model': model, 'max_tokens': 400, 'temperature': 0,
                                    'messages': [{'role': 'user', 'content': prompt}]})
            if r.status_code in (429, 500, 502, 503, 529):
                time.sleep(2 ** attempt * 5)
                continue
            r.raise_for_status()
            j = r.json()
            return ''.join(b.get('text', '') for b in j['content']), j['usage']['input_tokens'], j['usage']['output_tokens']
        raise RuntimeError(f'anthropic: gave up after retries ({r.status_code})')
    return ask


def parse_answer(raw):
    m = re.search(r'\{.*\}', raw or '', re.S)
    try:
        a = json.loads(m.group(0)) if m else {}
    except ValueError:
        a = {}
    return a if a.get('answer') in ('same', 'different', 'unsure') else {'answer': 'unsure', 'reason': 'unparseable reply'}


def resolve(site, decisions_path, out_path, ask, model, cache_path, budget_usd, usd_per_mtok_in, usd_per_mtok_out,
            limit=None, log=print):
    fetcher = HostQueueFetcher(site, cache_name=f'{site}.process', offline=True, log=lambda *a: None)
    cache_path = Path(cache_path)
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    spent, stats, out = 0.0, {'asked': 0, 'cached': 0, 'verified': 0, 'model_unsure': 0, 'quote_failed': 0, 'no_evidence': 0, 'budget_stop': 0}, []
    for n, d in enumerate(questions(decisions_path)):
        if limit is not None and n >= limit:
            break
        url_a, url_b = d['candidate']['url'], d['family']['canonical_url']
        ta, tb = page_text(fetcher, url_a), page_text(fetcher, url_b)
        rec = {'cache_key': d['cache_key'], 'kind': d['unsure_kind'], 'question': d['question'], 'url_a': url_a, 'url_b': url_b,
               'model': model, 'prompt_version': PROMPT_VERSION}
        if not ta or not tb:
            stats['no_evidence'] += 1
            out.append({**rec, 'answer': 'unsure', 'verified': False, 'reason': 'page snapshot missing'})
            continue
        prompt = PROMPT.format(question=d['question'], url_a=url_a, url_b=url_b, text_a=ta, text_b=tb)
        ck = hashlib.sha256(f'{model}|{PROMPT_VERSION}|{prompt}'.encode()).hexdigest()
        if ck in cache:
            a, cost, cached = cache[ck], 0.0, True
            stats['cached'] += 1
        else:
            if spent >= budget_usd:
                stats['budget_stop'] += 1
                out.append({**rec, 'answer': 'unsure', 'verified': False, 'reason': 'budget reached'})
                continue
            raw, tin, tout = ask(prompt)
            cost = (tin * usd_per_mtok_in + tout * usd_per_mtok_out) / 1e6
            spent += cost
            a = {**parse_answer(raw), 'tokens_in': tin, 'tokens_out': tout}
            cache[ck] = a
            cached = False
            stats['asked'] += 1
            if stats['asked'] % 50 == 0:
                cache_path.write_text(json.dumps(cache))
                log(f'  [{site}] asked {stats["asked"]}, spent ${spent:.2f}')
        ok = a['answer'] == 'unsure' or (quote_ok(a.get('quote_a'), ta) and quote_ok(a.get('quote_b'), tb))
        answer = a['answer'] if ok else 'unsure'
        outcome = 'quote_failed' if not ok else 'model_unsure' if answer == 'unsure' else 'verified'
        stats[outcome] = stats.get(outcome, 0) + 1
        out.append({**rec, 'answer': answer, 'model_answer': a['answer'], 'verified': ok and answer != 'unsure',
                    'quote_a': a.get('quote_a'), 'quote_b': a.get('quote_b'), 'reason': a.get('reason'),
                    'cost_usd': round(cost, 6), 'cached': cached})
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache))
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w') as f:
        for r in out:
            f.write(json.dumps(r) + '\n')
    stats['spent_usd'] = round(spent, 4)
    log(f'[{site}] resolver: {json.dumps(stats)}')
    return out, stats


def same_family_links(resolutions_path):
    """Verified "same" answers as (url_a, url_b, evidence) for grouping."""
    links = []
    with open(resolutions_path) as f:
        lines = f.readlines()
    for line in lines:
        r = json.loads(line)
        if r.get('verified') and r['answer'] == 'same':
            links.append((r['url_a'], r['url_b'],
                          f'R5 resolver ({r["model"]}): "{r["quote_a"]}" / "{r["quote_b"]}"'))
    return links
